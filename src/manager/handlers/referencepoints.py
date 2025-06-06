from datetime import datetime
from typing import Any

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from crud import referencepoint_crud
from manager.callbacks import (
    ManagerReferencepointCallback,
    ManagerRoadmapCallback,
)
from manager.constants import DATETIME_FORMAT, SKIP_COMMAND
from manager.keyboards.referencepoints import (
    get_referencepoint_menu_keyboard,
    referencepoint_editor_cancel_keyboard,
    select_referencepoint_keyboard,
)
from manager.states import EditReferencepointStates
from manager.utils import (
    generate_datetime_prompt,
    generate_referencepoint_text,
    send_or_edit_message,
)
from models.constants import ReferencePointType
from models.models import Notification, ReferencePoint

router = Router()


@router.callback_query(
    ManagerRoadmapCallback.filter(F.action == 'referencepoints_selector'),
)
async def manager_referencepoints_selector(
    callback: types.CallbackQuery,
    callback_data: ManagerRoadmapCallback,
    session: AsyncSession,
) -> None:
    """Меню выбора Контрольных точек."""
    referencepoints = await referencepoint_crud.get_multi_filtered(
        session,
        ReferencePoint.roadmap_id == callback_data.roadmap_id,
    )

    if not referencepoints:
        text = ('<b>Нет доступных Контрольных точек!</b>\n\n'
                'Добавьте их через редактор.')
    else:
        text = 'Выберите Контрольную точку:\n\n<b>Доступные точки:</b>'

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': select_referencepoint_keyboard(
            referencepoints,
            callback_data.intern_id,
        ),
    }
    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerReferencepointCallback.filter(F.action == 'select_referencepoint'),
)
async def manager_select_referencepoint(
    callback: types.CallbackQuery,
    callback_data: ManagerReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Меню управления Контрольной точкой."""
    referencepoint = await referencepoint_crud.get(
        callback_data.referencepoint_id,
        session,
        load_relations=True,
    )

    if not referencepoint:
        await callback.answer('Точка не найдена!', show_alert=True)
        return

    state_data = await state.get_data()
    text = generate_referencepoint_text(
        point=referencepoint,
        state_data=state_data,
    )
    reply_markup = get_referencepoint_menu_keyboard(
        referencepoint,
        intern_id=callback_data.intern_id,
    )

    await send_or_edit_message(
        callback=callback,
        message={'text': text, 'parse_mode': 'HTML',
                 'reply_markup': reply_markup},
    )


@router.callback_query(
    ManagerReferencepointCallback.filter(
        F.action == 'edit_referencepoint_name'),
)
async def manager_edit_referencepoint_name(
    callback: types.CallbackQuery,
    callback_data: ManagerReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование имени Контрольной точки."""
    referencepoint = await referencepoint_crud.get(
        callback_data.referencepoint_id,
        session,
    )

    if not referencepoint or not callback.message:
        return

    await state.set_state(EditReferencepointStates.editing_name)
    await state.update_data(
        referencepoint_id=callback_data.referencepoint_id,
        intern_id=callback_data.intern_id,
        editor_message_id=callback.message.message_id,
    )

    text = (
        '<i>Текущее название Контрольной точки:</i>\n'
        f'<b>{referencepoint.name}</b>\n\n'
        '<i>Введите новое название:</i>'
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': referencepoint_editor_cancel_keyboard(
            callback_data.referencepoint_id,
            callback_data.intern_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerReferencepointCallback.filter(F.action == 'block_referencepoint'),
)
async def manager_block_referencepoint(
    callback: types.CallbackQuery,
    callback_data: ManagerReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Блокировка/разблокировка Контрольной точки."""
    referencepoint = await referencepoint_crud.get(
        callback_data.referencepoint_id,
        session,
        relations_to_upload=[ReferencePoint.notification],
    )

    if not referencepoint:
        return

    new_block_status = not referencepoint.is_blocked
    referencepoint.is_blocked = new_block_status
    await session.commit()

    await state.update_data(is_blocked=new_block_status)
    state_data = await state.get_data()

    text = generate_referencepoint_text(
        point=referencepoint,
        state_data=state_data,
        changes=True,
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_referencepoint_menu_keyboard(
            referencepoint,
            intern_id=callback_data.intern_id,
            changes=True,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerReferencepointCallback.filter(F.action == 'edit_notification'),
)
async def manager_edit_notification_text(
    callback: types.CallbackQuery,
    callback_data: ManagerReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование уведомления в контрольной точке типа Уведомление."""
    referencepoint = await referencepoint_crud.get(
        callback_data.referencepoint_id,
        session,
        relations_to_upload=[ReferencePoint.notification],
    )

    if not referencepoint:
        return

    if not referencepoint.notification:
        new_notification = Notification(
            text='',
            need_feedback=False,
            feedbacks=[],
            links=[],
            servise_notes=[],
            reference_point=referencepoint,
        )
        session.add(new_notification)
        await session.commit()
        await session.refresh(referencepoint)

    await state.set_state(EditReferencepointStates.editing_notification_text)
    await state.update_data(
        referencepoint_id=referencepoint.id,
        intern_id=callback_data.intern_id,
        current_text=referencepoint.notification.text or '',
        editor_message_id=callback.message.message_id,
    )

    text = (
        '<i>Текущий текст уведомления:</i>\n'
        f'<b>{referencepoint.notification.text or "(пусто)"}</b>\n\n'
        '<i>Введите новый текст уведомления:</i>'
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': referencepoint_editor_cancel_keyboard(
            callback_data.referencepoint_id,
            callback_data.intern_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.message(EditReferencepointStates.editing_name)
async def manager_process_new_referencepoint_name(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового названия Контрольной точки."""
    data = await state.get_data()

    referencepoint = await referencepoint_crud.get(
        obj_id=data['referencepoint_id'],
        session=session,
        relations_to_upload=[ReferencePoint.notification],
    )

    if not referencepoint or not message.text:
        await state.clear()
        return

    new_name = message.text.strip()
    referencepoint.name = new_name
    await session.commit()
    await message.delete()

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['editor_message_id'],
        text=generate_referencepoint_text(
            point=referencepoint,
            state_data={**data, 'new_name': new_name},
            changes=True,
        ),
        parse_mode='HTML',
        reply_markup=get_referencepoint_menu_keyboard(
            referencepoint,
            intern_id=data['intern_id'],
            changes=True,
        ),
    )
    await state.clear()


@router.message(EditReferencepointStates.editing_notification_text)
async def manager_process_new_notification_text(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового текста уведомления."""
    data = await state.get_data()

    referencepoint = await referencepoint_crud.get(
        data['referencepoint_id'],
        session,
        relations_to_upload=[ReferencePoint.notification],
    )

    if not referencepoint or not message.text:
        await state.clear()
        return

    if not referencepoint.notification:
        referencepoint.notification = Notification()
        session.add(referencepoint.notification)

    new_text = message.text.strip()
    referencepoint.notification.text = new_text
    await session.commit()
    await message.delete()

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['editor_message_id'],
        text=generate_referencepoint_text(
            point=referencepoint,
            state_data={**data, 'new_notification_text': new_text},
            changes=True,
        ),
        parse_mode='HTML',
        reply_markup=get_referencepoint_menu_keyboard(
            referencepoint,
            intern_id=data['intern_id'],
            changes=True,
        ),
    )
    await state.clear()


@router.callback_query(
    ManagerReferencepointCallback.filter(
        F.action.in_(['edit_trigger_datetime', 'edit_check_datetime']),
    ),
)
async def manager_edit_datetime(
    callback: types.CallbackQuery,
    callback_data: ManagerReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование полей даты."""
    referencepoint = await referencepoint_crud.get(
        callback_data.referencepoint_id,
        session,
    )

    if not referencepoint or not callback.message:
        return

    is_trigger = callback_data.action == 'edit_trigger_datetime'
    field_name = 'дата срабатывания' if is_trigger else 'дедлайн проверки'

    await state.set_state(
        EditReferencepointStates.editing_trigger_datetime if is_trigger
        else EditReferencepointStates.editing_check_datetime,
    )
    await state.update_data(
        referencepoint_id=callback_data.referencepoint_id,
        intern_id=callback_data.intern_id,
        editor_message_id=callback.message.message_id,
    )

    current_value = (
        referencepoint.trigger_datetime if is_trigger
        else referencepoint.check_datetime
    )
    message = generate_datetime_prompt(
        current_value=current_value,
        field_name=field_name,
        callback_data=callback_data,
        skip_allowed=not is_trigger,
    )

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerReferencepointCallback.filter(F.action == 'edit_reminder'),
)
async def manager_edit_reminder(
    callback: types.CallbackQuery,
    callback_data: ManagerReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование дней напоминания."""
    referencepoint = await referencepoint_crud.get(
        callback_data.referencepoint_id,
        session,
    )

    if not referencepoint or not callback.message:
        return

    await state.set_state(EditReferencepointStates.editing_reminder)
    await state.update_data(
        referencepoint_id=callback_data.referencepoint_id,
        intern_id=callback_data.intern_id,
        editor_message_id=callback.message.message_id,
    )

    text = (
        '<i>Текущее количество дней для напоминания:</i>\n'
        f'<b>{referencepoint.reminder_days_before} дн.</b>\n\n'
        '<i>Введите новое количество дней (от 0 до 365):</i>'
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': referencepoint_editor_cancel_keyboard(
            callback_data.referencepoint_id,
            callback_data.intern_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.message(EditReferencepointStates.editing_trigger_datetime)
async def manager_process_trigger_datetime(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка новой даты срабатывания."""
    await message.delete()

    data = await state.get_data()
    referencepoint = await referencepoint_crud.get(
        obj_id=data['referencepoint_id'],
        session=session,
        relations_to_upload=[ReferencePoint.notification],
    )

    if not referencepoint:
        await state.clear()
        return

    try:
        new_datetime = datetime.strptime(message.text.strip(), DATETIME_FORMAT)
        await state.update_data(
            trigger_datetime=new_datetime.strftime(DATETIME_FORMAT),
        )

        state_data = await state.get_data()
        state_data['trigger_datetime'] = datetime.strptime(
            state_data['trigger_datetime'],
            DATETIME_FORMAT,
        )

        text = generate_referencepoint_text(
            point=referencepoint,
            state_data=state_data,
            changes=True,
        )

        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['editor_message_id'],
            text=text,
            parse_mode='HTML',
            reply_markup=get_referencepoint_menu_keyboard(
                referencepoint,
                intern_id=data['intern_id'],
                changes=True,
            ),
        )
    except ValueError:
        current_date = (
            referencepoint.trigger_datetime.strftime(DATETIME_FORMAT)
            if referencepoint.trigger_datetime else "не указано"
        )
        error_text = (
            '<i>Текущая дата срабатывания:</i>\n'
            f'<b>{current_date}</b>\n\n'
            '<i>Введите новую дату в формате ДД.ММ.ГГГГ ЧЧ:ММ</i>'
            '\n\n❌ Неверный формат даты'
        )
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['editor_message_id'],
            text=error_text,
            parse_mode='HTML',
            reply_markup=referencepoint_editor_cancel_keyboard(
                data['referencepoint_id'],
                data['intern_id'],
            ),
        )


@router.message(EditReferencepointStates.editing_check_datetime)
async def manager_process_check_datetime(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового дедлайна проверки."""
    await message.delete()

    data = await state.get_data()
    referencepoint = await referencepoint_crud.get(
        obj_id=data['referencepoint_id'],
        session=session,
        relations_to_upload=[ReferencePoint.notification],
    )

    if not referencepoint:
        await state.clear()
        return

    user_input = message.text.strip().lower()
    try:
        if user_input == SKIP_COMMAND.lower():
            await state.update_data(check_datetime=None)
        else:
            new_datetime = datetime.strptime(user_input, DATETIME_FORMAT)
            await state.update_data(
                check_datetime=datetime.strftime(
                    new_datetime,
                    DATETIME_FORMAT,
                ),
            )

        state_data = await state.get_data()

        check_dt_value = state_data.get('check_datetime')
        if check_dt_value is not None:
            state_data['check_datetime'] = datetime.strptime(
                check_dt_value,
                DATETIME_FORMAT,
            )

        text = generate_referencepoint_text(
            point=referencepoint,
            state_data=state_data,
            changes=True,
        )

        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['editor_message_id'],
            text=text,
            parse_mode='HTML',
            reply_markup=get_referencepoint_menu_keyboard(
                referencepoint,
                intern_id=data['intern_id'],
                changes=True,
            ),
        )
    except ValueError:
        current_date = (
            referencepoint.check_datetime.strftime(DATETIME_FORMAT)
            if referencepoint.check_datetime else "не указано"
        )
        error_text = (
            '<i>Текущий дедлайн проверки:</i>\n'
            f'<b>{current_date}</b>\n\n'
            '<i>Введите новую дату в формате ДД.ММ.ГГГГ ЧЧ:ММ</i>\n'
            f'<i>Или введите "{SKIP_COMMAND}" чтобы оставить пустым</i>'
            '\n\n❌ Неверный формат даты'
        )
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['editor_message_id'],
            text=error_text,
            parse_mode='HTML',
            reply_markup=referencepoint_editor_cancel_keyboard(
                data['referencepoint_id'],
                data['intern_id'],
            ),
        )


@router.message(EditReferencepointStates.editing_reminder)
async def manager_process_reminder_days(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка дней напоминания."""
    data = await state.get_data()
    referencepoint = await referencepoint_crud.get(
        obj_id=data['referencepoint_id'],
        session=session,
        relations_to_upload=[ReferencePoint.notification],
    )

    if not referencepoint:
        await state.clear()
        return

    try:
        days = int(message.text.strip())
        if not 0 <= days <= 365:
            raise ValueError

        await state.update_data(reminder_days_before=days)

        state_data = await state.get_data()
        text = generate_referencepoint_text(
            point=referencepoint,
            state_data=state_data,
            changes=True,
        )

        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['editor_message_id'],
            text=text,
            parse_mode='HTML',
            reply_markup=get_referencepoint_menu_keyboard(
                referencepoint,
                intern_id=data['intern_id'],
                changes=True,
            ),
        )
        await message.delete()
    except ValueError:
        error_text = (
            '<i>Текущее количество дней:</i>\n'
            f'<b>{referencepoint.reminder_days_before} дн.</b>\n\n'
            '<i>Введите число от 0 до 365:</i>'
            '\n\n❌ Некорректное значение'
        )
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['editor_message_id'],
            text=error_text,
            parse_mode='HTML',
            reply_markup=referencepoint_editor_cancel_keyboard(
                data['referencepoint_id'],
                data['intern_id'],
            ),
        )


async def update_referencepoint_from_data(
        referencepoint: ReferencePoint,
        data: dict[str, Any],
) -> None:
    """Обновляет поля referencepoint на основе данных из state."""
    if 'new_name' in data:
        referencepoint.name = data['new_name']
    if 'is_blocked' in data:
        referencepoint.is_blocked = data['is_blocked']
    if 'reminder_days_before' in data:
        referencepoint.reminder_days_before = data['reminder_days_before']

    await update_datetime_field(referencepoint, 'trigger_datetime', data)
    await update_datetime_field(referencepoint, 'check_datetime', data)

    if (referencepoint.point_type == ReferencePointType.NOTIFICATION
            and 'new_notification_text' in data):
        if not referencepoint.notification:
            referencepoint.notification = Notification(
                text=data['new_notification_text'],
            )
        else:
            referencepoint.notification.text = data['new_notification_text']


async def update_datetime_field(
        referencepoint: ReferencePoint,
        field_name: str,
        data: dict[str, Any],
) -> None:
    """Обновляет дату в referencepoint, если есть в data."""
    if field_name in data:
        dt_str = data[field_name]
        if dt_str:
            setattr(referencepoint, field_name,
                    datetime.strptime(dt_str, DATETIME_FORMAT))
        else:
            setattr(referencepoint, field_name, None)


@router.callback_query(
    ManagerReferencepointCallback.filter(F.action == 'save_referencepoint'),
)
async def manager_save_referencepoint(
    callback: types.CallbackQuery,
    callback_data: ManagerReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Сохранение изменений в чекпоинте."""
    data = await state.get_data()
    referencepoint = await referencepoint_crud.get(
        callback_data.referencepoint_id,
        session,
        relations_to_upload=[ReferencePoint.notification],
    )

    if not referencepoint:
        await state.clear()
        return

    await update_referencepoint_from_data(referencepoint, data)

    await session.commit()
    await state.clear()

    await callback.answer('✅ Изменения сохранены!', show_alert=True)

    referencepoint = await referencepoint_crud.get(
        callback_data.referencepoint_id,
        session,
        relations_to_upload=[ReferencePoint.notification],
    )

    text = generate_referencepoint_text(
        point=referencepoint,
        state_data={},
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_referencepoint_menu_keyboard(
            referencepoint,
            intern_id=callback_data.intern_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)
