from datetime import datetime

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from admin.keyboards import admin_keyboard
from crud import invite_crud, user_crud
from intern.handlers.notifications import handle_reference_point_type
from intern.keyboards import intern_keyboard
from intern.utils import get_active_reference_points_for_user
from manager.handlers.interns import intern_missed_deadline
from manager.handlers.manager_menu import manager_menu
from models.constants import UserRole
from models.models import User

from .constants import (
    ADMIN_HELP_TEXT,
    ADMIN_WELCOME_MESSAGE,
    INTERN_HELP_TEXT,
    INTERN_WELCOME_MESSAGE,
    INVALID_LINK_MESSAGE,
    INVALID_ROLE_MESSAGE,
    INVATATION_MESSAGE,
    MANAGER_WELCOME_MESSAGE,
    YOU_ARE_BLOCKED_MESSAGE,
)

router = Router(name='start_help')


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    session: AsyncSession,
    command: CommandObject,
    user: User,
) -> Message:
    """Обрабатывает старт.

    1) Если в args передан token — обрабатываем приглашение.
    2) Иначе, если user нет — не авторизован.
    3) Иначе — отправляем приветствие.
    """
    args = command.args
    if args:
        invit = await invite_crud.get(obj_id=args, session=session)
        if invit and not invit.is_used and invit.expires_at > datetime.now():
            invited_user = await user_crud.get(invit.user_id, session)
            await user_crud.update(
                invited_user,
                {'tg_id': message.from_user.id},
                session,
            )
            invit.is_used = True
            session.add(invit)
            await session.commit()
            return await message.answer(
                INVATATION_MESSAGE,
            )
        return await message.answer(
            INVALID_LINK_MESSAGE,
        )
    if not user.is_active:
        return await message.reply(YOU_ARE_BLOCKED_MESSAGE)

    #  проверяем роль
    match user.role:
        case UserRole.ADMIN:
            return await message.answer(
                ADMIN_WELCOME_MESSAGE,
                reply_markup=admin_keyboard,
            )
        case UserRole.MANAGER:
            await message.answer(MANAGER_WELCOME_MESSAGE)
            return await manager_menu(message)
        case UserRole.USER:
            intern = await user_crud.get_user_by_tg_id(
                session,
                message.chat.id,
            )
            reference_points = await get_active_reference_points_for_user(
                intern.id,
                session,
            )
            if not reference_points:
                return await message.answer(
                    INTERN_WELCOME_MESSAGE,
                    reply_markup=intern_keyboard,
                )
            scheduler = AsyncIOScheduler(timezone=intern.timezone)
            for reference_point in reference_points:
                scheduler.add_job(
                    handle_reference_point_type,
                    'date',
                    run_date=reference_point.trigger_datetime,
                    kwargs={
                        'bot': message.bot,
                        'reference_point': reference_point,
                        'user': intern,
                        'scheduler': scheduler,
                    },
                )
                if reference_point.check_datetime:
                    scheduler.add_job(
                        intern_missed_deadline,
                        'date',
                        run_date=reference_point.check_datetime,
                        kwargs={
                            'bot': message.bot,
                            'manager_tg_id': await user_crud.get_tgid_by_id(
                                intern.manager_id,
                                session,
                            ),
                            'reference_point_name': reference_point.name,
                            'name': intern.first_name,
                            'surname': intern.last_name,
                        },
                        id=str(reference_point.id),
                    )
            scheduler.start()
            return await message.answer(
                INTERN_WELCOME_MESSAGE,
                reply_markup=intern_keyboard,
            )
        case _:
            return await message.answer(INVALID_ROLE_MESSAGE)


@router.message(Command('help'))
async def cmd_help(
    message: Message,
    user: User,
) -> Message:
    """Показывает доступные команды и меню."""
    if not user.is_active:
        return await message.reply(YOU_ARE_BLOCKED_MESSAGE)

    match user.role:
        case UserRole.ADMIN:
            text = ADMIN_HELP_TEXT
            keyboard = admin_keyboard
        # case UserRole.MANAGER:
        #     text = 'Привет Манагер'
        #     keyboard = manager_keyboard
        case UserRole.USER:
            text = INTERN_HELP_TEXT
            keyboard = intern_keyboard
        case _:
            text = INVALID_ROLE_MESSAGE
            keyboard = None

    return await message.answer(
        text,
        reply_markup=keyboard,
    )
