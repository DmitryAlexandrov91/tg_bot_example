from datetime import datetime
from typing import Any, Awaitable, Callable, Optional, Union

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from sqlalchemy.ext.asyncio import AsyncSession

from crud import roadmap_crud, template_roadmap_crud
from manager.callbacks import ManagerReferencepointCallback
from manager.constants import DATETIME_FORMAT, POINT_TYPE_NAMES, SKIP_COMMAND
from manager.keyboards.referencepoints import (
    referencepoint_editor_cancel_keyboard,
)
from manager.keyboards.roadmaps import (
    get_roadmap_editor_menu_keyboard,
)
from manager.keyboards.template_roadmaps import (
    get_templateroadmap_editor_menu_keyboard,
)
from models.constants import ReferencePointType
from models.models import (
    ReferencePoint,
    RoadMap,
    TemplateReferencePoint,
    TemplateRoadMap,
)


async def send_or_edit_message(
    callback: types.CallbackQuery,
    message: dict[str, Any],
) -> None:
    """Редактирует сообщение или отсылает новое."""
    if callback.message and not isinstance(
        callback.message,
        types.InaccessibleMessage,
    ):
        await callback.message.edit_text(**message)
    else:
        await callback.answer(**message)


async def get_templateroadmap(
    templateroadmap_id: int,
    session: AsyncSession,
    callback: Optional[types.CallbackQuery] = None,
    message: Optional[types.Message] = None,
) -> Optional[TemplateRoadMap]:
    """Получение Шаблона дорожной карты."""
    templateroadmap = await template_roadmap_crud.get(
        templateroadmap_id,
        session,
        load_relations=True,
    )

    if not templateroadmap:
        error_msg = 'Шаблон дорожной карты не найден!'
        if callback:
            await callback.answer(error_msg, show_alert=True)
        elif message:
            await message.answer(error_msg)
    return templateroadmap


async def get_intern_roadmap(
    intern_id: int,
    session: AsyncSession,
    callback: Optional[types.CallbackQuery] = None,
) -> Optional[RoadMap]:
    """Получает активную дорожную карту стажёра."""
    roadmap = await roadmap_crud.get_user_roadmap(
        intern_id=intern_id,
        session=session,
    )

    if not roadmap and callback:
        await callback.answer(
            'У стажёра нет активной дорожной карты!',
            show_alert=True,
        )
    return roadmap


def generate_roadmap_editor_text(
    roadmap: Union[RoadMap, TemplateRoadMap],
    state_data: dict,
    changes: bool = False,
    edit_mode: bool = False,
) -> str:
    """Генератор текста для редактора дорожной карты.

    roadmap: объект RoadMap или TemplateRoadMap,
    state_data: данные контекста,
    changes: флаг наличия изменений в ДК,
    edit_mode: режим редактирования.
    """
    is_template = isinstance(roadmap, TemplateRoadMap)

    state_data = state_data or {}

    name = state_data.get('new_name', roadmap.name)
    description = state_data.get('new_description', roadmap.description)

    status_line = ''
    if is_template:
        is_blocked = state_data.get('is_blocked', roadmap.is_blocked)
        status_line = (
            f'<b><i>Статус</i></b>: '
            f'{"🔒 Заблокирована" if is_blocked else "🔓 Активна"}'
            f'{" <i>(изменено)</i>" if "is_blocked" in state_data else ""}\n'
        )

    text = [
        '<b>Редактированиe: ' if edit_mode else '<b>',
        'Шаблон Дорожной карты</b>\n\n' if is_template
        else 'Дорожная карта</b>\n\n',
        '<b>‼️Есть несохранённые изменения!‼️</b>\n\n' if changes else '',
        f'<b><i>Название</i></b>: {name}',
        ' <i>(изменено)</i>' if 'new_name' in state_data else '',
        '\n',
        f'<b><i>Описание</i></b>: {description}',
        ' <i>(изменено)</i>' if 'new_description' in state_data else '',
        '\n',
        status_line,
        f'<b><i>Контрольных точек</i></b>: {len(roadmap.reference_points)}',
    ]

    return ''.join(text)


async def process_templateroadmap_field_update(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    state_to_set: State,
    obj_field: str | None,
    data_field: str,
) -> None:
    """Обработка полей Шаблона дорожной карты."""
    data = await state.get_data()

    templateroadmap = await get_templateroadmap(
        data['templateroadmap_id'],
        session,
        message=message,
    )

    if not templateroadmap:
        return

    update_data = {
        data_field: message.text if message.text != obj_field else None,
    }
    await state.update_data(**update_data)

    await state.set_state(state_to_set)
    await message.delete()

    data = await state.get_data()
    text = generate_roadmap_editor_text(
        templateroadmap,
        data,
        changes=True,
    )

    await message.bot.edit_message_text(
        text=text,
        parse_mode='HTML',
        chat_id=message.chat.id,
        message_id=data.get('editor_message_id'),
        reply_markup=get_templateroadmap_editor_menu_keyboard(
            templateroadmap=templateroadmap,
            changes='new_name' in data or 'new_description' in data,
        ),
    )


async def process_roadmap_field_update(
    message: types.Message,
    state: FSMContext,
    session: AsyncSession,
    state_to_set: State,
    obj_field: str,
    data_field: str,
) -> None:
    """Обработка полей Дорожной карты."""
    data = await state.get_data()
    roadmap = await roadmap_crud.get(
        data['roadmap_id'],
        session,
        relations_to_upload=[RoadMap.user_associations],
    )
    if not roadmap or not roadmap.user_associations:
        return

    update_data = {
        data_field: message.text if message.text != obj_field else None,
    }
    await state.update_data(**update_data)

    await state.set_state(state_to_set)
    await message.delete()

    data = await state.get_data()

    text = generate_roadmap_editor_text(
        roadmap=roadmap,
        state_data=data,
        changes=True,
        edit_mode=True,
    )

    intern_id = roadmap.user_associations[0].user_id

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data['editor_message_id'],
        text=text,
        parse_mode='HTML',
        reply_markup=get_roadmap_editor_menu_keyboard(
            roadmap=roadmap,
            intern_id=intern_id,
            changes='new_name' in data or 'new_description' in data,
        ),
    )


def generate_referencepoint_text(
    point: Union[TemplateReferencePoint, ReferencePoint],
    state_data: Optional[dict] = None,
    changes: bool = False,
    edit_mode: bool = False,
) -> str:
    """Генератор текста для редактора контрольных точек.

    point: объект Referencepoint или TemplateReferencepoint,
    state_data: данные контекста,
    changes: флаг наличия изменений в ДК,
    edit_mode: режим редактирования.
    """
    if state_data is None:
        state_data = {}

    is_template = isinstance(point, TemplateReferencePoint)

    name = state_data.get('new_name', point.name)
    point_type = state_data.get('new_point_type', point.point_type)
    is_blocked = state_data.get('is_blocked', point.is_blocked)

    trigger_time = ""
    check_time = ""
    reminder_days = ""

    if not is_template:
        trigger_time = format_datetime(
            state_data.get(
                'trigger_datetime',
                getattr(point, 'trigger_datetime', None),
            ),
        )
        check_time = format_datetime(
            state_data.get(
                'check_datetime',
                getattr(point, 'check_datetime', None),
            ),
        )
        reminder_days = str(
            state_data.get(
                'reminder_days_before',
                getattr(point, 'reminder_days_before', 'не указано'),
            )) + ' дн.'

    notification_text = ''
    if point_type == ReferencePointType.NOTIFICATION:
        notification = getattr(point, 'notification', None)
        notification_text = (
            notification.text if notification and notification.text
            else '⚠️ Текст уведомления не задан'
        )
        if 'new_notification_text' in state_data:
            notification_text = state_data['new_notification_text']

    text_parts = [
        '<b>Редактирование контрольной точки</b>\n\n' if edit_mode
        else '<b>Контрольная точка</b>\n\n',
        '<b>‼️Есть несохранённые изменения!‼️</b>\n\n' if changes else '',
        f'<b><i>Название</i></b>: {name}',
        ' <i>(изменено)</i>' if 'new_name' in state_data else '',
        '\n',
        f'<b><i>Тип точки</i></b>: {POINT_TYPE_NAMES.get(point_type)}',
        ' <i>(изменено)</i>' if 'new_point_type' in state_data else '',
        '\n',
    ]

    if not is_template:
        text_parts.extend([
            f'<b><i>Дата срабатывания</i></b>: {trigger_time}',
            ' <i>(изменено)</i>' if 'trigger_datetime' in state_data else '',
            '\n',

            f'<b><i>Дедлайн проверки</i></b>: {check_time}',
            ' <i>(изменено)</i>' if 'check_datetime' in state_data else '',
            '\n',

            f'<b><i>Напоминание за</i></b>: {reminder_days}',
            ' <i>(изменено)</i>' if 'reminder_days_before' in state_data
            else '',
            '\n',
        ])

    text_parts.extend([
        '<b><i>Статус</i></b>: ',
        f'{"🔒 Заблокирована" if is_blocked else "🔓 Активна"}',
        ' <i>(изменено)</i>' if 'is_blocked' in state_data else '',
    ])

    if point_type == ReferencePointType.NOTIFICATION:
        notification_status = (
            ' <i>(изменено)</i>' if (
                'new_notification_text' in state_data
            ) else ''
        )
        text_parts.extend([
            '\n<b><i>Текст уведомления</i></b>:\n',
            f'{notification_text}{notification_status}',
        ])

    return ''.join(text_parts)


def format_datetime(dt: Optional[datetime]) -> str:
    """Форматирует datetime в строку или возвращает 'не указано'."""
    if isinstance(dt, datetime):
        return dt.strftime(DATETIME_FORMAT)
    return 'не указано'


async def generate_referencepoint_creator_text(
    points_to_process: list,
    entered_data: dict,
    current_point_name: Optional[str] = None,
    current_field: Optional[str] = None,
    error_message: Optional[str] = None,
    edit_mode: bool = False,
) -> str:
    """Генератор текста для сообщения редактирования контрольных точек."""
    text = '<b>Ввод данных контрольных точек</b>\n\n'

    for i, (_, name) in enumerate(points_to_process):
        point_data = entered_data.get(str(i), {})
        trigger_time = point_data.get('trigger_time', '<i>не указано</i>')
        check_time = point_data.get('check_datetime', '<i>не указано</i>')
        reminder = point_data.get('reminder_days_before', '<i>не указано</i>')

        text += (
            f'{i+1}. <b>{name}</b>\n'
            f'   - Время запуска: <b>{trigger_time}</b>\n'
            f'   - Дедлайн проверки: <b>{check_time}</b>\n'
            f'   - Напоминание за (дней): <b>{reminder}</b>\n\n'
        )

    if current_point_name and current_field:
        field_names = {
            'trigger_time': 'время запуска события (ДД.ММ.ГГГГ ЧЧ:ММ)',
            'check_datetime': (
                f'дедлайн проверки (ДД.ММ.ГГГГ ЧЧ:ММ или "{SKIP_COMMAND}")'
            ),
            'reminder_days_before': (
                f'количество дней для напоминания (число или "{SKIP_COMMAND}")'
            ),
        }
        text += (f'<b><i>Введите {field_names[current_field]} '
                 f'для точки "{current_point_name}":</i></b>')

    if error_message:
        text += f'\n\n<b>‼️ {error_message} ‼️</b>'

    return text


async def process_datetime_input(
    message: types.Message,
    session: AsyncSession,
    state: FSMContext,
    field: str,
    next_field: str,
    required: bool,
    *,
    data_input_func: Callable[
        [types.Message, AsyncSession, FSMContext],
        Awaitable[Any],
    ],
) -> None:
    """Обработка ввода даты."""
    data = await state.get_data()
    current_error = None
    user_input = message.text.strip().lower()

    if not required and user_input == SKIP_COMMAND:
        datetime_str = SKIP_COMMAND
    else:
        try:
            dt = datetime.strptime(user_input, DATETIME_FORMAT)
            datetime_str = dt.strftime(DATETIME_FORMAT)
        except ValueError:
            current_error = 'invalid_format'

    if current_error:
        error_message = 'Некорректный формат даты!' if required else (
            'Некорректный формат даты! Введите ДД.ММ.ГГГГ ЧЧ:ММ или '
            f'"{SKIP_COMMAND}"'
        )

        if data.get('last_error') == current_error:
            await message.delete()
            return

        await state.update_data(last_error=current_error)
        text = await generate_referencepoint_creator_text(
            points_to_process=data['points_to_process'],
            entered_data=data.get('entered_data', {}),
            current_point_name=data['current_point_name'],
            current_field=field,
            error_message=error_message,
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
    point_data[field] = datetime_str
    entered_data[index] = point_data

    await state.update_data(
        entered_data=entered_data,
        last_error=None,
        current_field=next_field,
    )

    await data_input_func(message, session, state)
    await message.delete()


def generate_datetime_prompt(
    current_value: Optional[datetime],
    field_name: str,
    callback_data: ManagerReferencepointCallback,
    skip_allowed: bool = False,
) -> dict[str, Any]:
    """Генератор сообщения редактирования даты."""
    current = current_value.strftime(
        DATETIME_FORMAT,
    ) if current_value else SKIP_COMMAND
    text = (
        f'<i>Текущая {field_name}:</i>\n'
        f'<b>{current}</b>\n\n'
        f'<i>Введите новую дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ</i>\n'
    )
    if skip_allowed:
        text += f'<i>Или введите {SKIP_COMMAND} чтобы оставить пустым</i>'

    return {
        'text': text,
        'parse_mode': 'HTML',
        'reply_markup': referencepoint_editor_cancel_keyboard(
            callback_data.referencepoint_id,
            callback_data.intern_id,
        ),
    }
