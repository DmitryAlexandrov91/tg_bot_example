from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from crud import template_reference_point_crud
from manager.callbacks import (
    ManagerTemplateReferencepointCallback,
    ManagerTemplateRoadmapCallback,
)
from manager.keyboards.template_referencepoints import (
    get_templatereferencepoint_menu_keyboard,
    select_templatereferencepoint_keyboard,
    templatereferencepoint_editor_cancel_keyboard,
)
from manager.states import EditTemplateReferencepointStates
from manager.utils import (
    generate_referencepoint_text,
    send_or_edit_message,
)
from models.constants import ReferencePointType
from models.models import TemplateNotification, TemplateReferencePoint

router = Router()


@router.callback_query(
    ManagerTemplateRoadmapCallback.filter(
        F.action == 'templatereferencepoints_selector',
    ),
)
async def manager_templatereferencepoints_selector(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateRoadmapCallback,
    session: AsyncSession,
) -> None:
    """Меню Редактора Шаблонов контрольных точек.

    Выбор Шаблона контрольной точки.
    """
    templatereferencepoints = (
        await template_reference_point_crud.get_multi_filtered(
            session,
            (TemplateReferencePoint.templateroadmap_id
             == callback_data.templateroadmap_id),
        ))

    if not templatereferencepoints:
        text = ('<b>Нет доступных Шаблонов контрольных точек!</b>\n\n'
                'Обратитесь к администратору.')
        templatereferencepoints = []
    else:
        text = 'Выберите Шаблон контрольной точки\n\n<b>Доступные шаблоны:</b>'

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': select_templatereferencepoint_keyboard(
            templatereferencepoints,
            callback_data.templateroadmap_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateReferencepointCallback.filter(
        F.action == 'select_templatereferencepoint',
    ),
)
async def manager_select_templatereferencepoint(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Меню Шаблона контрольной точки."""
    templatereferencepoint = await template_reference_point_crud.get(
        callback_data.templatereferencepoint_id,
        session,
        load_relations=True,
    )

    if not templatereferencepoint:
        return

    state_data = await state.get_data()
    text = generate_referencepoint_text(
        point=templatereferencepoint,
        state_data=state_data,
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_templatereferencepoint_menu_keyboard(
            templatereferencepoint,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateReferencepointCallback.filter(
        F.action == 'templatereferencepoint_edit_name',
    ),
)
async def manager_edit_templatereferencepoint_name(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование имени Шаблона контрольной точки."""
    templatereferencepoint = await template_reference_point_crud.get(
        callback_data.templatereferencepoint_id,
        session,
    )

    if not templatereferencepoint or not callback.message:
        return

    await state.set_state(EditTemplateReferencepointStates.editing_name)
    await state.update_data(
        templatereferencepoint_id=callback_data.templatereferencepoint_id,
        editor_message_id=callback.message.message_id,
    )

    text = (
        '<i>Текущее название Шаблона контрольной точки:</i>\n'
        f'<b>{templatereferencepoint.name}</b>\n\n'
        '<i>Введите новое название Шаблона контрольной точки:</i>'
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': templatereferencepoint_editor_cancel_keyboard(
            callback_data.templatereferencepoint_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateReferencepointCallback.filter(
        F.action == 'block_templatereferencepoint',
    ),
)
async def manager_block_templatereferencepoint(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Блокировка Шаблона контрольной точки."""
    templatereferencepoint = await template_reference_point_crud.get(
        callback_data.templatereferencepoint_id,
        session,
        load_relations=True,
    )

    if not templatereferencepoint:
        return

    new_block_status = not templatereferencepoint.is_blocked
    templatereferencepoint.is_blocked = new_block_status
    await session.commit()

    await state.update_data(is_blocked=new_block_status)
    state_data = await state.get_data()

    text = generate_referencepoint_text(
        point=templatereferencepoint,
        state_data=state_data,
        changes=True,
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_templatereferencepoint_menu_keyboard(
            templatereferencepoint,
            changes=True,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerTemplateReferencepointCallback.filter(
        F.action == 'templatereferencepoint_edit_notification',
    ),
)
async def manager_edit_templatenotification_text(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование уведомления в контрольной точке типа Уведомление."""
    templatereferencepoint = await template_reference_point_crud.get(
        callback_data.templatereferencepoint_id,
        session,
        relations_to_upload=[TemplateReferencePoint.notification],
    )

    if not templatereferencepoint:
        return

    if not templatereferencepoint.notification:
        new_notification = TemplateNotification(
            text='',
            need_feedback=False,
            feedbacks=[],
            links=[],
            servise_notes=[],
            reference_point=templatereferencepoint,
        )
        session.add(new_notification)
        await session.commit()
        await session.refresh(templatereferencepoint)

    await state.set_state(
        EditTemplateReferencepointStates.editing_notification_text,
    )
    await state.update_data(
        templatereferencepoint_id=templatereferencepoint.id,
        current_text=templatereferencepoint.notification.text or '',
        editor_message_id=callback.message.message_id,
    )

    text = (
        '<i>Текущий текст уведомления:</i>\n'
        f'<b>{templatereferencepoint.notification.text or "(пусто)"}</b>\n\n'
        '<i>Введите новый текст уведомления:</i>'
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': templatereferencepoint_editor_cancel_keyboard(
            callback_data.templatereferencepoint_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.message(EditTemplateReferencepointStates.editing_name)
async def manager_process_new_templatereferencepoint_name(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового названия Шаблона контрольной точки."""
    data = await state.get_data()
    point_id = data['templatereferencepoint_id']

    templatereferencepoint = await template_reference_point_crud.get(
        obj_id=point_id,
        session=session,
        relations_to_upload=[TemplateReferencePoint.notification],
    )

    if not templatereferencepoint or not message.text:
        await state.clear()
        return

    new_name = message.text.strip()
    templatereferencepoint.name = new_name
    await session.commit()
    await message.delete()

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['editor_message_id'],
        text=generate_referencepoint_text(
            point=templatereferencepoint,
            state_data={**data, 'new_name': new_name},
            changes=True,
        ),
        parse_mode='HTML',
        reply_markup=get_templatereferencepoint_menu_keyboard(
            templatereferencepoint,
            changes=True,
        ),
    )
    await state.clear()


@router.message(EditTemplateReferencepointStates.editing_notification_text)
async def manager_process_new_notification_text(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового текста уведомления для контрольной точки."""
    data = await state.get_data()

    templatereferencepoint = await template_reference_point_crud.get(
        data['templatereferencepoint_id'],
        session,
        relations_to_upload=[TemplateReferencePoint.notification],
    )

    if not templatereferencepoint or not message.text:
        await state.clear()
        return

    if not templatereferencepoint.notification:
        templatereferencepoint.notification = TemplateNotification()
        session.add(templatereferencepoint.notification)

    new_text = message.text.strip()
    templatereferencepoint.notification.text = new_text
    await session.commit()
    await message.delete()

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['editor_message_id'],
        text=generate_referencepoint_text(
            point=templatereferencepoint,
            state_data={**data, 'new_notification_text': new_text},
            changes=True,
        ),
        parse_mode='HTML',
        reply_markup=get_templatereferencepoint_menu_keyboard(
            templatereferencepoint,
            changes=True,
        ),
    )
    await state.clear()


@router.callback_query(
    ManagerTemplateReferencepointCallback.filter(
        F.action == 'save_templatereferencepoint',
    ),
)
async def manager_save_templatereferencepoint_changes(
    callback: types.CallbackQuery,
    callback_data: ManagerTemplateReferencepointCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Сохранение изменений Шаблона контрольной точки в БД."""
    data = await state.get_data()
    templatereferencepoint = await template_reference_point_crud.get(
        callback_data.templatereferencepoint_id,
        session,
        relations_to_upload=[TemplateReferencePoint.notification],
    )

    if not templatereferencepoint:
        await callback.answer(
            'Шаблон контрольной точки не найден!',
            show_alert=True,
        )
        return

    if 'new_name' in data:
        templatereferencepoint.name = data['new_name']
    if 'new_point_type' in data:
        templatereferencepoint.point_type = data['new_point_type']
    if 'is_blocked' in data:
        templatereferencepoint.is_blocked = data['is_blocked']

    if (templatereferencepoint.point_type == ReferencePointType.NOTIFICATION
            and 'new_notification_text' in data):
        if not templatereferencepoint.notification:
            templatereferencepoint.notification = TemplateNotification(
                text=data['new_notification_text'],
            )
        else:
            templatereferencepoint.notification.text = data[
                'new_notification_text'
            ]

    await session.commit()
    await state.clear()
    await callback.answer(
        '✅ Изменения сохранены!',
        show_alert=True,
    )

    templatereferencepoint = await template_reference_point_crud.get(
        callback_data.templatereferencepoint_id,
        session,
        load_relations=True,
    )

    if not templatereferencepoint:
        return

    text = generate_referencepoint_text(
        point=templatereferencepoint,
        state_data={},
        changes=False,
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_templatereferencepoint_menu_keyboard(
            templatereferencepoint,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)
