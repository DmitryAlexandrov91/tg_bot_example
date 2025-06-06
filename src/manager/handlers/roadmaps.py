from datetime import datetime

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import false
from sqlalchemy.ext.asyncio import AsyncSession

from crud import (
    roadmap_crud,
    template_notification_crud,
    template_reference_point_crud,
    template_roadmap_crud,
    user_crud,
)
from intern.handlers.notifications import handle_reference_point_type
from intern.utils import get_active_reference_point_for_user
from manager.callbacks import (
    ManagerAssignRoadmapCallback,
    ManagerInternCallback,
    ManagerRoadmapCallback,
)
from manager.constants import DATETIME_FORMAT, ERROR_MESSAGES, SKIP_COMMAND
from manager.handlers.interns import intern_missed_deadline
from manager.keyboards.roadmaps import (
    assign_templateroadmap_keyboard,
    get_roadmap_editor_menu_keyboard,
    referencepoint_cancel_upload_keyboard,
    referencepoints_finish_upload_keyboard,
    roadmap_editor_cancel_keyboard,
)
from manager.states import AssignRoadmapStates, EditRoadmapStates
from manager.utils import (
    generate_referencepoint_creator_text,
    generate_roadmap_editor_text,
    get_intern_roadmap,
    get_templateroadmap,
    process_datetime_input,
    process_roadmap_field_update,
    send_or_edit_message,
)
from models.constants import ReferencePointType
from models.models import (
    Notification,
    ReferencePoint,
    RoadMap,
    TemplateReferencePoint,
    TemplateRoadMap,
    User,
    UserRoadMap,
)

from .interns import process_intern_select

router = Router()


@router.callback_query(
    ManagerInternCallback.filter(F.action == 'manager_intern_create_roadmap'),
)
async def manager_select_templateroadmap(
    callback: types.CallbackQuery,
    callback_data: ManagerInternCallback,
    session: AsyncSession,
    user: User,
) -> None:
    """Выбор доступного шаблона дорожной карты для назначения Стажёру."""
    templateroadmaps = (
        await template_roadmap_crud.get_multi_filtered(
            session,
            TemplateRoadMap.restaurant_id == user.restaurant_id,
            TemplateRoadMap.is_blocked == false(),
        ))

    if not templateroadmaps:
        text = ('<b>Нет доступных Шаблонов дорожных карт!</b>\n\n'
                'Обратитесь к администратору.')
        templateroadmaps = []
    else:
        text = 'Выберите Шаблон дорожной карты\n\n<b>Доступные шаблоны:</b>'

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': assign_templateroadmap_keyboard(
            intern_id=callback_data.intern_id,
            templateroadmaps=templateroadmaps,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerAssignRoadmapCallback.filter(F.action == 'assign_roadmap'),
)
async def manager_assign_roadmap_to_intern(
    callback: types.CallbackQuery,
    callback_data: ManagerAssignRoadmapCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Назначение дорожной карты Стажёру.

    Создает объект Дорожной карты из Шаблона дорожной карты.
    """
    templateroadmap = await get_templateroadmap(
        callback_data.templateroadmap_id,
        session,
        callback=callback,
    )

    if not templateroadmap:
        return

    tmppoints = await template_reference_point_crud.get_multi_filtered(
        session,
        TemplateReferencePoint.is_blocked == false(),
        TemplateReferencePoint.templateroadmap_id == templateroadmap.id,
    )

    await state.update_data(
        intern_id=callback_data.intern_id,
        templateroadmap_id=callback_data.templateroadmap_id,
        points_to_process=[(point.id, point.name) for point in tmppoints],
        current_point_index=0,
        entered_data={},
        current_field='trigger_time',
        last_bot_message_id=callback.message.message_id,
        roadmap_name=templateroadmap.name,
        roadmap_description=templateroadmap.description,
        last_error=None,
    )
    await referencepoint_data_input(callback.message, session, state)


async def referencepoint_data_input(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Запрос данных для Контрольной точки."""
    data = await state.get_data()
    points = data['points_to_process']
    index = data['current_point_index']
    current_field = data.get('current_field', 'trigger_time')

    if index >= len(points):
        text = await generate_referencepoint_creator_text(
            points_to_process=data['points_to_process'],
            entered_data=data['entered_data'],
        )
        text += '\n✅ Все точки успешно добавлены!'

        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['last_bot_message_id'],
            text=text,
            parse_mode='HTML',
            reply_markup=referencepoints_finish_upload_keyboard(
                intern_id=data['intern_id'],
            ),
        )

        return

    point_id, point_name = points[index]
    await state.update_data(
        current_point_id=point_id,
        current_point_name=point_name,
        current_field=current_field,
    )

    if current_field == 'trigger_time':
        await state.set_state(AssignRoadmapStates.waiting_for_trigger_time)
    elif current_field == 'check_datetime':
        await state.set_state(AssignRoadmapStates.waiting_for_check_datetime)
    else:
        await state.set_state(AssignRoadmapStates.waiting_for_reminder_days)

    text = await generate_referencepoint_creator_text(
        points_to_process=data['points_to_process'],
        entered_data=data.get('entered_data', {}),
        current_point_name=point_name,
        current_field=current_field,
    )

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['last_bot_message_id'],
        text=text,
        parse_mode='HTML',
        reply_markup=referencepoint_cancel_upload_keyboard(
            intern_id=data['intern_id'],
        ),
    )


@router.message(AssignRoadmapStates.waiting_for_trigger_time)
async def process_trigger_time_input(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Обработка введенного времени запуска."""
    await process_datetime_input(
        message,
        session,
        state,
        field='trigger_time',
        next_field='check_datetime',
        required=True,
        data_input_func=referencepoint_data_input,
    )


@router.message(AssignRoadmapStates.waiting_for_check_datetime)
async def process_check_datetime_input(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Обработка введенного дедлайна."""
    await process_datetime_input(
        message,
        session,
        state,
        field='check_datetime',
        next_field='reminder_days_before',
        required=False,
        data_input_func=referencepoint_data_input,
    )


@router.message(AssignRoadmapStates.waiting_for_reminder_days)
async def process_reminder_days_input(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Обработка введенного количества дней до напоминания."""
    data = await state.get_data()
    current_error = None
    user_input = message.text.strip().lower()

    if user_input == SKIP_COMMAND:
        reminder_days = None
    else:
        try:
            reminder_days = int(user_input)
            if reminder_days < 0:
                current_error = 'negative_value'
        except ValueError:
            current_error = 'invalid_format'

    if current_error:
        if data.get('last_error') == current_error:
            await message.delete()
            return
        await state.update_data(last_error=current_error)
        text = await generate_referencepoint_creator_text(
            points_to_process=data['points_to_process'],
            entered_data=data.get('entered_data', {}),
            current_point_name=data['current_point_name'],
            current_field='reminder_days_before',
            error_message=ERROR_MESSAGES[current_error],
        )
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data['last_bot_message_id'],
            text=text,
            parse_mode='HTML',
        )
        await message.delete()
        return

    index = str(data['current_point_index'])
    entered_data = data.get('entered_data', {})
    point_data = entered_data.get(index, {})
    point_data['reminder_days_before'] = (
        str(reminder_days) if reminder_days is not None else SKIP_COMMAND
    )
    entered_data[index] = point_data

    await state.update_data(
        entered_data=entered_data,
        last_error=None,
    )

    await state.update_data(
        current_point_index=data['current_point_index'] + 1,
        current_field='trigger_time',
    )
    await referencepoint_data_input(message, session, state)
    await message.delete()


@router.callback_query(
    ManagerInternCallback.filter(F.action == 'save_roadmap'),
)
async def manager_save_roadmap_to_intern(
    callback: types.CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Завершение назначения Дорожной карты Стажёру.

    Сохранение в БД Дорожной карты,
    Сохранение в БД Контрольных точек.
    """
    data = await state.get_data()
    entered_data = data.get('entered_data', {})

    new_roadmap = RoadMap(
        name=data['roadmap_name'],
        description=data['roadmap_description'],
        is_active=True,
    )
    session.add(new_roadmap)
    await session.flush()

    session.add(UserRoadMap(
        user_id=data['intern_id'],
        roadmap=new_roadmap,
    ))

    for index, (point_id, _) in enumerate(data['points_to_process']):
        point_data = entered_data.get(str(index), {})
        template_point = await template_reference_point_crud.get(
            point_id,
            session,
        )

        trigger_time = datetime.strptime(
            point_data['trigger_time'],
            DATETIME_FORMAT,
        ) if 'trigger_time' in point_data else None

        check_datetime = (
            datetime.strptime(point_data['check_datetime'], DATETIME_FORMAT)
            if ('check_datetime' in point_data
                and point_data['check_datetime'] != SKIP_COMMAND)
            else None
        )

        reminder_days = (
            int(point_data['reminder_days_before'])
            if ('reminder_days_before' in point_data
                and point_data['reminder_days_before'] != SKIP_COMMAND)
            else None
        )

        reference_point = ReferencePoint(
            name=template_point.name,
            point_type=template_point.point_type,
            order_execution=template_point.order_execution,
            trigger_datetime=trigger_time,
            check_datetime=check_datetime,
            reminder_days_before=reminder_days,
            roadmap_id=new_roadmap.id,
        )
        session.add(reference_point)
        await session.flush()

        if template_point.point_type == ReferencePointType.NOTIFICATION:
            template_notification = (
                await template_notification_crud.get_by_referencepoint_id(
                    referencepoint_id=template_point.id,
                    session=session,
                )
            )

            if template_notification:
                new_notification = Notification(
                    text=template_notification.text,
                    need_feedback=template_notification.need_feedback,
                    feedbacks=template_notification.feedbacks or [],
                    links=template_notification.links or [],
                    servise_notes=template_notification.servise_notes or [],
                    referencepoint_id=reference_point.id,
                )
                session.add(new_notification)

        intern = await roadmap_crud.get_user_id_by_roadmap_id(
            new_roadmap.id, session,
        )
        new_reference_point = await get_active_reference_point_for_user(
            intern.id,
            session,
        )
        scheduler = AsyncIOScheduler(timezone=intern.timezone)
        scheduler.add_job(
            handle_reference_point_type,
            'date',
            run_date=new_reference_point.trigger_datetime,
            kwargs={
                'bot': callback.bot,
                'reference_point': new_reference_point,
                'user': intern,
                'scheduler': scheduler,
            },
        )
        if new_reference_point.check_datetime:
            scheduler.add_job(
                intern_missed_deadline,
                'date',
                run_date=new_reference_point.check_datetime,
                kwargs={
                    'bot': callback.message.bot,
                    'manager_tg_id': await user_crud.get_tgid_by_id(
                        intern.manager_id, session,
                    ),
                    'reference_point_name': new_reference_point.name,
                    'name':intern.first_name,
                    'surname': intern.last_name,
                },
                id=str(new_reference_point.id),
            )
        scheduler.start()
        await session.commit()
        await callback.answer('✅ Дорожная карта сохранена!', show_alert=True)
        await state.clear()


@router.callback_query(
    ManagerInternCallback.filter(F.action == 'cancel_roadmap'),
)
async def cancel_roadmap_input(
    callback: types.CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Отмена создания Дорожной карты."""
    data = await state.get_data()

    callback_data = ManagerInternCallback(
        action='manager_intern_actions',
        intern_id=data.get('intern_id'),
    )

    await state.clear()
    await callback.answer(
        'Изменения отменены',
        show_alert=True,
    )

    await process_intern_select(
        callback=callback,
        callback_data=callback_data,
        session=session,
    )


@router.callback_query(
    ManagerInternCallback.filter(F.action == 'manager_intern_edit_roadmap'),
)
async def manager_edit_roadmap(
    callback: types.CallbackQuery,
    callback_data: ManagerInternCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Меню редактора дорожной карты стажёра."""
    roadmap = await get_intern_roadmap(
        intern_id=callback_data.intern_id,
        session=session,
        callback=callback,
    )

    if not roadmap or not callback.message:
        return

    await state.update_data(
        intern_id=callback_data.intern_id,
        roadmap_id=roadmap.id,
        editor_message_id=callback.message.message_id,
    )
    await state.set_state(EditRoadmapStates.selecting_action)

    state_data = await state.get_data()
    text = generate_roadmap_editor_text(
        roadmap=roadmap,
        state_data=state_data,
        edit_mode=True,
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_roadmap_editor_menu_keyboard(
            roadmap=roadmap,
            intern_id=callback_data.intern_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerRoadmapCallback.filter(F.action == 'edit_roadmap_name'),
    EditRoadmapStates.selecting_action,
)
async def manager_edit_roadmap_name(
    callback: types.CallbackQuery,
    callback_data: ManagerRoadmapCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование названия дорожной карты стажёра."""
    data = await state.get_data()
    roadmap = await roadmap_crud.get(
        data['roadmap_id'],
        session,
        load_relations=True,
    )

    if not roadmap:
        return

    await state.set_state(EditRoadmapStates.editing_name)

    text = (
        '<i>Текущее название дорожной карты:</i>\n'
        f'<b>{roadmap.name}</b>\n\n'
        '<i>Введите новое название:</i>'
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': roadmap_editor_cancel_keyboard(
            intern_id=callback_data.intern_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.callback_query(
    ManagerRoadmapCallback.filter(F.action == 'edit_roadmap_description'),
    EditRoadmapStates.selecting_action,
)
async def manager_edit_roadmap_description(
    callback: types.CallbackQuery,
    callback_data: ManagerRoadmapCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Редактирование описания дорожной карты стажёра."""
    data = await state.get_data()
    roadmap = await roadmap_crud.get(data['roadmap_id'], session)

    if not roadmap:
        return

    await state.set_state(EditRoadmapStates.editing_description)

    text = (
        '<i>Текущее описание дорожной карты:</i>\n'
        f'<b>{roadmap.description}</b>\n\n'
        '<i>Введите новое описание:</i>'
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': roadmap_editor_cancel_keyboard(
            intern_id=callback_data.intern_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)


@router.message(EditRoadmapStates.editing_name)
async def manager_process_new_roadmap_name(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового названия дорожной карты."""
    data = await state.get_data()
    roadmap = await roadmap_crud.get(data['roadmap_id'], session)

    if not roadmap:
        await state.clear()
        return

    await process_roadmap_field_update(
        message=message,
        state=state,
        session=session,
        state_to_set=EditRoadmapStates.selecting_action,
        obj_field=roadmap.name,
        data_field='new_name',
    )


@router.message(EditRoadmapStates.editing_description)
async def manager_process_new_roadmap_description(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нового описания дорожной карты."""
    data = await state.get_data()
    roadmap = await roadmap_crud.get(data['roadmap_id'], session)

    if not roadmap:
        await state.clear()
        return

    await process_roadmap_field_update(
        message=message,
        state=state,
        session=session,
        state_to_set=EditRoadmapStates.selecting_action,
        obj_field=roadmap.description,
        data_field='new_description',
    )


@router.callback_query(
    ManagerRoadmapCallback.filter(F.action == 'save_edited_roadmap'),
    EditRoadmapStates.selecting_action,
)
async def manager_save_roadmap_changes(
    callback: types.CallbackQuery,
    callback_data: ManagerInternCallback,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    """Сохранение изменений дорожной карты стажёра."""
    data = await state.get_data()
    roadmap = await roadmap_crud.get(data['roadmap_id'], session)

    if not roadmap:
        await callback.answer(
            'Дорожная карта не найдена!',
            show_alert=True,
        )
        return

    if 'new_name' in data:
        roadmap.name = data['new_name']
    if 'new_description' in data:
        roadmap.description = data['new_description']

    await session.commit()
    await state.clear()
    await callback.answer(
        '✅ Изменения сохранены!',
        show_alert=True,
    )

    roadmap = await roadmap_crud.get(data['roadmap_id'], session)
    text = generate_roadmap_editor_text(
        roadmap=roadmap,
        state_data={},
    )

    message = {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': get_roadmap_editor_menu_keyboard(
            roadmap=roadmap,
            intern_id=callback_data.intern_id,
        ),
    }

    await send_or_edit_message(callback=callback, message=message)
