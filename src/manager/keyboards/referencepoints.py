from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from manager.callbacks import (
    ManagerInternCallback,
    ManagerReferencepointCallback,
    ManagerRoadmapCallback,
    ManagerStartCallback,
)
from manager.constants import (
    BACK,
    BACK_TO_MENU,
    POINT_TYPE_NAMES,
)
from models.constants import ReferencePointType
from models.models import ReferencePoint


def select_referencepoint_keyboard(
    referencepoints: List[ReferencePoint],
    intern_id: int,
) -> InlineKeyboardMarkup:
    """Выбор контрольной точки."""
    builder = InlineKeyboardBuilder()

    for point in sorted(referencepoints, key=lambda x: x.order_execution):
        point_type = POINT_TYPE_NAMES.get(point.point_type)
        builder.button(
            text=(
                f'{point.order_execution}: {point.name} ({point_type})'
                f'{" (🔒)" if point.is_blocked else ""}'
            ),
            callback_data=ManagerReferencepointCallback(
                intern_id=intern_id,
                referencepoint_id=point.id,
                action='select_referencepoint',
            ),
        )

    builder.button(
        text=BACK,
        callback_data=ManagerInternCallback(
            action='manager_intern_edit_roadmap',
            intern_id=intern_id,
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


def get_referencepoint_menu_keyboard(
    referencepoint: ReferencePoint,
    intern_id: int,
    changes: bool = False,
) -> InlineKeyboardMarkup:
    """Меню контрольной точки."""
    builder = InlineKeyboardBuilder()

    if changes:
        builder.button(
            text='💾 Сохранить',
            callback_data=ManagerReferencepointCallback(
                intern_id=intern_id,
                referencepoint_id=referencepoint.id,
                action='save_referencepoint',
            ),
        )

    builder.button(
        text='Редактировать название',
        callback_data=ManagerReferencepointCallback(
            intern_id=intern_id,
            referencepoint_id=referencepoint.id,
            action='edit_referencepoint_name',
        ),
    )

    builder.button(
        text='Редактировать дату срабатывания',
        callback_data=ManagerReferencepointCallback(
            referencepoint_id=referencepoint.id,
            intern_id=intern_id,
            action='edit_trigger_datetime',
        ),
    )

    builder.button(
        text='Редактировать дедлайн',
        callback_data=ManagerReferencepointCallback(
            referencepoint_id=referencepoint.id,
            intern_id=intern_id,
            action='edit_check_datetime',
        ),
    )

    builder.button(
        text='Редактировать время напоминания',
        callback_data=ManagerReferencepointCallback(
            referencepoint_id=referencepoint.id,
            intern_id=intern_id,
            action='edit_reminder',
        ),
    )

    builder.button(
        text=('🔒 Заблокировать' if not referencepoint.is_blocked
              else '🔓 Разблокировать'),
        callback_data=ManagerReferencepointCallback(
            intern_id=intern_id,
            referencepoint_id=referencepoint.id,
            action='block_referencepoint',
        ),
    )

    if referencepoint.point_type == ReferencePointType.NOTIFICATION:
        builder.button(
            text='Редактировать уведомление',
            callback_data=ManagerReferencepointCallback(
                intern_id=intern_id,
                referencepoint_id=referencepoint.id,
                action='edit_notification',
            ),
        )

    if changes:
        back_button_callback = ManagerStartCallback(
            action='show_unsaved_alert',
        )
    else:
        back_button_callback = ManagerRoadmapCallback(
            roadmap_id=referencepoint.roadmap_id,
            intern_id=intern_id,
            action='referencepoints_selector',
        )

    builder.button(
        text=BACK,
        callback_data=back_button_callback,
    )

    builder.button(
        text=BACK_TO_MENU,
        callback_data=ManagerStartCallback(
            action='show_unsaved_alert' if changes else 'back_to_menu',
        ),
    )

    builder.adjust(1)
    return builder.as_markup()


def referencepoint_editor_cancel_keyboard(
    referencepoint_id: int,
    intern_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура отмены редактирования."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='❌ Отменить',
        callback_data=ManagerReferencepointCallback(
            referencepoint_id=referencepoint_id,
            intern_id=intern_id,
            action='select_referencepoint',
        ),
    )

    builder.adjust(1)
    return builder.as_markup()
