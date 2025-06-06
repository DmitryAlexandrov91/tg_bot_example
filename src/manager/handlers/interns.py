from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from crud.roadmap import roadmap_crud
from crud.users import user_crud
from manager.callbacks import (
    ManagerInternCallback,
    ManagerStartCallback,
)
from manager.constants import (
    CHOOSE_ACTION_STRING,
    ENTER_YOUR_MESSAGE,
    INTERN_BANNED,
    INTERN_END_EDUCATION,
    INTERN_HASNT_EDUCATION,
    INTERN_MESSAGE,
    INTERN_MISSED_DEADLINE,
    INTERN_SCALE_ROADMAP,
)
from manager.keyboards.interns import (
    get_ban_or_end_education_keyboard,
    get_intern_answer_on_action,
    get_intern_keyboard,
    get_interns_actions_keyboard,
)
from manager.states import ManagerMessage
from models.models import User

router = Router()


@router.callback_query(
    ManagerStartCallback.filter(F.action == 'manager_interns'),
)
async def get_interns(
    callback: types.CallbackQuery,
    session: AsyncSession,
    user: User,
) -> None:
    """Обработка кнопки управления Стажёрами."""
    interns = await user_crud.get_managers_interns(user.id, session)

    if not interns:
        text = ('<b>За Вами не закреплены Стажёры!</b>\n\n'
                'Обратитесь к администратору.')
    else:
        text = 'Выберите Стажёра\n\n<b>Ваши Стажёры:</b>'

    await callback.message.edit_text(
        text,
        parse_mode='HTML',
        reply_markup=get_intern_keyboard(interns),
    )
    await callback.answer()


@router.callback_query(ManagerInternCallback.filter(
    F.action == 'manager_intern_actions',
))
async def process_intern_select(
    callback: types.CallbackQuery,
    callback_data: ManagerInternCallback,
    session: AsyncSession,
) -> None:
    """Обработка процессов связанных со стажером."""
    intern = await user_crud.get(
        obj_id=callback_data.intern_id,
        session=session,
        relations_to_upload=[User.roadmaps],
    )

    if not intern:
        return

    await callback.message.edit_text(
        text=CHOOSE_ACTION_STRING.format(
            name=intern.first_name,
            surname=intern.last_name,
        ),
        parse_mode='HTML',
        reply_markup=get_interns_actions_keyboard(
            intern_id=callback_data.intern_id,
            intern_has_roadmap=bool(intern.roadmaps),
        ),
    )
    await callback.answer()


@router.callback_query(
    ManagerInternCallback.filter(F.action == 'manager_intern_message'),
)
async def write_message_to_intern(
    callback: types.CallbackQuery,
    callback_data: ManagerInternCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Метод получения сообщения менеджера и tg id стажера."""
    intern_tg_id = await user_crud.get_tgid_by_id(
        callback_data.intern_id, session,
    )
    intern = await user_crud.get(
        obj_id=callback_data.intern_id,
        session=session,
        relations_to_upload=[User.roadmaps],
    )

    if not intern:
        return
    await callback.message.edit_text(
        text=ENTER_YOUR_MESSAGE,
        parse_mode='HTML',
        reply_markup=get_intern_answer_on_action(
            callback_data.intern_id,
            intern.first_name,
            intern.last_name,
        ),
    )
    await callback.answer()
    await state.update_data(
        intern_tg_id=intern_tg_id,
        intern_first_name=intern.first_name,
        intern_last_name=intern.last_name,
    )
    await state.set_state(ManagerMessage.message)


@router.message(ManagerMessage.message, F.text)
async def get_manager_message(
    message: types.Message, state: FSMContext,
) -> None:
    """Метод отправляет сообщения менеджера стажеру."""
    await state.update_data(message=message.text)
    manager_message = await state.get_data()
    await state.clear()
    await message.delete()
    await message.bot.send_message(
        manager_message['intern_tg_id'],
        INTERN_MESSAGE.format(
            name=manager_message['intern_first_name'],
            surname=manager_message['intern_last_name'],
            message=manager_message['message'],
        ),
    )
    await message.answer('Сообщение было успешно отправлено!')


@router.callback_query(
    ManagerInternCallback.filter(F.action == 'manager_intern_menagement'),
)
async def management_intern(
    callback: types.CallbackQuery,
    callback_data: ManagerInternCallback,
    session: AsyncSession,
) -> None:
    """Метод управления стажером. Бан и досрочное завершение обучения."""
    intern = await user_crud.get(
        obj_id=callback_data.intern_id,
        session=session,
    )

    if not intern:
        return

    await callback.message.edit_text(
        text=CHOOSE_ACTION_STRING.format(
            name=intern.first_name,
            surname=intern.last_name,
        ),
        parse_mode='HTML',
        reply_markup=get_ban_or_end_education_keyboard(
            callback_data.intern_id),
    )
    await callback.answer()


@router.callback_query(
    ManagerInternCallback.filter(F.action == 'ban_intern'),
)
async def ban_intern(
    callback: types.CallbackQuery,
    callback_data: ManagerInternCallback,
    session: AsyncSession,
) -> None:
    """Метод блокировки стажера."""
    await user_crud.ban_user(callback_data.intern_id, session)
    intern = await user_crud.get(
        obj_id=callback_data.intern_id,
        session=session,
    )
    if not intern:
        return
    await callback.message.edit_text(
        text=INTERN_BANNED.format(
            name=intern.first_name,
            surname=intern.last_name,
        ),
        parse_mode='HTML',
        reply_markup=get_intern_answer_on_action(
            callback_data.intern_id,
            intern.first_name,
            intern.last_name,
        ),
    )
    await callback.answer()


@router.callback_query(
    ManagerInternCallback.filter(F.action == 'end_education_intern'),
)
async def end_education_intern(
    callback: types.CallbackQuery,
    callback_data: ManagerInternCallback,
    session: AsyncSession,
) -> None:
    """Метод досрочного завершения обучения стажера."""
    await user_crud.end_education_intern(callback_data.intern_id, session)
    intern = await user_crud.get(
        obj_id=callback_data.intern_id,
        session=session,
    )
    if not intern:
        return
    await callback.message.edit_text(
        text=INTERN_END_EDUCATION.format(
            name=intern.first_name,
            surname=intern.last_name,
        ),
        parse_mode='HTML',
        reply_markup=get_intern_answer_on_action(
            callback_data.intern_id,
            intern.first_name,
            intern.last_name,
        ),
    )
    await callback.answer()


@router.callback_query(
    ManagerInternCallback.filter(F.action == 'manager_intern_education'),
)
async def education_progress(
    callback: types.CallbackQuery,
    callback_data: ManagerInternCallback,
    session: AsyncSession,
) -> None:
    """Метод проверки прогресса обучения стажера."""
    roadmap = await roadmap_crud.get_users_roadmap(
        callback_data.intern_id, session,
    )
    intern = await user_crud.get(
            obj_id=callback_data.intern_id,
            session=session,
        )
    if not intern:
        return

    if not roadmap:
        list_of_points = INTERN_HASNT_EDUCATION.format(
            name=intern.first_name,
            surname=intern.last_name,
        )
    else:
        list_of_points = INTERN_SCALE_ROADMAP.format(
            name=intern.first_name,
            surname=intern.last_name,
            roadmap_name=roadmap.name,
        )

        for reference_point in roadmap.get_all_points:
            list_of_points = (
                ' '.join((
                    list_of_points,
                    '\n\n',
                    reference_point.name,
                    (
                        '✅' if reference_point.is_completed is True
                        else '❌'
                    ),
                ))
            )

    await callback.message.edit_text(
        text=list_of_points,
        parse_mode='HTML',
        reply_markup=get_intern_answer_on_action(
            callback_data.intern_id,
            intern.first_name,
            intern.last_name,
        ),
    )
    await callback.answer()


async def intern_missed_deadline(
    bot: Bot,
    manager_tg_id: int,
    reference_point_name: str,
    name: str,
    surname: str,
) -> types.Message:
    """Отправляет уведомление менеджеру, что стажер просрочил задание."""
    await bot.send_message(
        manager_tg_id, INTERN_MISSED_DEADLINE.format(
            name=name,
            surname=surname,
            reference_point_name=reference_point_name,
        ),
    )
