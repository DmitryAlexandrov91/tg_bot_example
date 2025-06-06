from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from manager.callbacks import (
    ManagerStartCallback,
    ManagerTemplateReferencepointCallback,
    ManagerTemplateRoadmapCallback,
)
from manager.constants import (
    BACK,
    BACK_TO_MENU,
    POINT_TYPE_NAMES,
)
from models.constants import ReferencePointType
from models.models import TemplateReferencePoint


def select_templatereferencepoint_keyboard(
        templatereferencepoints: List[TemplateReferencePoint],
        templateroadmap_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора Шаблона контрольной точки."""
    builder = InlineKeyboardBuilder()

    sorted_templatereferencepoints = sorted(
        templatereferencepoints,
        key=lambda x: x.order_execution,
    )

    for templatereferencepoint in sorted_templatereferencepoints:
        point_type = POINT_TYPE_NAMES.get(
            templatereferencepoint.point_type,
        )
        builder.button(
            text=(
                f'{templatereferencepoint.order_execution}: '
                f'{templatereferencepoint.name} '
                f'({point_type})'
                f'{" (🔒)" if templatereferencepoint.is_blocked else ""}'
            ),
            callback_data=ManagerTemplateReferencepointCallback(
                templatereferencepoint_id=templatereferencepoint.id,
                action='select_templatereferencepoint',
            ),
        )

    builder.button(
        text=BACK,
        callback_data=ManagerTemplateRoadmapCallback(
            templateroadmap_id=templateroadmap_id,
            action='select',
        ),
    )

    builder.button(
        text=BACK_TO_MENU,
        callback_data=ManagerStartCallback(
            action='back_to_menu',
        ),
    )

    builder.adjust(1)
    return builder.as_markup()


def get_templatereferencepoint_menu_keyboard(
        templatereferencepoint: TemplateReferencePoint,
        changes: bool = False,
) -> InlineKeyboardMarkup:
    """Клавиатура управления Шаблоном контрольной точки."""
    builder = InlineKeyboardBuilder()

    if changes:
        builder.button(
            text='💾 Сохранить изменения',
            callback_data=ManagerTemplateReferencepointCallback(
                templatereferencepoint_id=templatereferencepoint.id,
                action='save_templatereferencepoint',
            ),
        )

    builder.button(
        text='Редактировать название',
        callback_data=ManagerTemplateReferencepointCallback(
            templatereferencepoint_id=templatereferencepoint.id,
            action='templatereferencepoint_edit_name',
        ),
    )

    block_status = (
        '🔓 Разблокировать' if templatereferencepoint.is_blocked
        else '🔒 Заблокировать'
    )
    builder.button(
        text=block_status,
        callback_data=ManagerTemplateReferencepointCallback(
            templatereferencepoint_id=templatereferencepoint.id,
            action='block_templatereferencepoint',
        ),
    )

    if templatereferencepoint.point_type == ReferencePointType.NOTIFICATION:
        builder.button(
            text='Редактировать уведомление',
            callback_data=ManagerTemplateReferencepointCallback(
                templatereferencepoint_id=templatereferencepoint.id,
                action='templatereferencepoint_edit_notification',
            ),
        )

    if templatereferencepoint.point_type == ReferencePointType.TEST:
        builder.button(
            text='Управление тестом',
            callback_data=ManagerTemplateReferencepointCallback(
                templatereferencepoint_id=templatereferencepoint.id,
                action='templatereferencepoint_edit_quiz',
            ),
        )

    builder.button(
        text=BACK,
        callback_data=ManagerTemplateRoadmapCallback(
            templateroadmap_id=templatereferencepoint.templateroadmap_id,
            action=(
                'show_unsaved_alert' if changes
                else 'templatereferencepoints_selector'
            ),
        ),
    )

    builder.button(
        text=BACK_TO_MENU,
        callback_data=ManagerStartCallback(
            action='show_unsaved_alert' if changes else 'back_to_menu',
        ),
    )

    builder.adjust(1)
    return builder.as_markup()


def templatereferencepoint_editor_cancel_keyboard(
    templatereferencepoint_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура управления Редактором Контрольной точки."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='❌ Отменить',
        callback_data=ManagerTemplateReferencepointCallback(
            templatereferencepoint_id=templatereferencepoint_id,
            action='select_templatereferencepoint',
        ),
    )

    builder.adjust(1)
    return builder.as_markup()
