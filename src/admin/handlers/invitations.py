from datetime import datetime, timedelta
from json import dumps

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin.keyboards import build_user_id_select_keyboard
from admin.states.users import InvitationForm
from admin.utils import get_unique_link_token, json_deserial, json_serial
from crud import invite_crud, user_crud
from models.models import User

router = Router(name='invitations')


@router.message(Command('get_invite'))
async def cmd_get_invite(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начало создание ссылки-приглашения. Устанавливает текущее время."""
    await state.clear()
    await state.update_data(
        created_at=dumps(datetime.now(), default=json_serial),
    )
    users = await user_crud.get_multi(
        session,
        options=[selectinload(User.restaurant)],
    )
    if not users:
        await message.answer('Нет пользователей.')
        return
    await message.answer(
        'Выберите пользователя, для которого нужно создать приглашение:',
        reply_markup=build_user_id_select_keyboard(
            users,
            prefix='invite_user',
        ),
    )


@router.callback_query(F.data.startswith('invite_user:'))
async def proc_user_id(
    call: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка ID стажера. Запрашивает время действия ссылки."""
    user_id = int(call.data.split(':', 1)[1])
    await state.update_data(user_id=user_id)
    await call.message.edit_reply_markup()
    await call.message.answer('Введите срок действия ссылки в днях:')
    await state.set_state(InvitationForm.expires_at)


@router.message(InvitationForm.expires_at)
async def proc_expires_at(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка времени действия ссылки. Создание ссылки-приглашения."""
    expires_at = datetime.now() + timedelta(days=int(message.text))
    await state.update_data(
        expires_at=dumps(expires_at, default=json_serial),
    )
    link_token = await get_unique_link_token(session)
    await state.update_data(link_token=link_token)
    data = await state.get_data()
    data['created_at'] = json_deserial(data['created_at'])
    data['expires_at'] = json_deserial(data['expires_at'])
    try:
        invite = await invite_crud.create(data, session)
    except IntegrityError as error:
        await message.answer(
            'Конфликт данных при сохранении.',
            {error},
        )
        return
    await message.answer(
        f'Для пользователя #{invite.user_id} создана ссылка-приглашение:',
    )
    await message.answer(
        f'https://t.me/smena_trainee_bot?start={invite.link_token}',
    )
    await state.clear()


@router.message(F.text == 'Сгенерировать приглашение')
async def alias_create_invitation(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Кнопка генерации ссылки-приглашения."""
    await cmd_get_invite(message, state, session)
