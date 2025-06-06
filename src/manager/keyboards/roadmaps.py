from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from manager.callbacks import (
    ManagerAssignRoadmapCallback,
    ManagerInternCallback,
    ManagerRoadmapCallback,
    ManagerStartCallback,
)
from manager.constants import (
    BACK,
    BACK_TO_MENU,
)
from models.models import RoadMap, TemplateRoadMap


def assign_templateroadmap_keyboard(
        templateroadmaps: List[TemplateRoadMap],
        intern_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора Шаблона дорожной карты для назначения."""
    builder = InlineKeyboardBuilder()

    for templateroadmap in templateroadmaps:
        builder.button(
            text=f'{templateroadmap.name}',
            callback_data=ManagerAssignRoadmapCallback(
                templateroadmap_id=templateroadmap.id,
                intern_id=intern_id,
                action='assign_roadmap',
            ),
        )

    builder.button(
        text=BACK,
        callback_data=ManagerInternCallback(
            action='manager_intern_actions',
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


def referencepoint_cancel_upload_keyboard(
    intern_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура управления Редактором Контрольной точки."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='❌ Отменить',
        callback_data=ManagerInternCallback(
            action='cancel_roadmap',
            intern_id=intern_id,
        ),
    )

    builder.adjust(1)
    return builder.as_markup()


def referencepoints_finish_upload_keyboard(
    intern_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура после добавления контрольных точек."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='💾 Сохранить изменения',
        callback_data=ManagerInternCallback(
            action='save_roadmap',
            intern_id=intern_id,
        ),
    )

    builder.button(
        text='❌ Отменить',
        callback_data=ManagerInternCallback(
            action='cancel_roadmap',
            intern_id=intern_id,
        ),
    )

    builder.button(
        text=BACK,
        callback_data=ManagerInternCallback(
            action='manager_intern_actions',
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


def get_roadmap_editor_menu_keyboard(
    roadmap: RoadMap,
    intern_id: int,
    changes: bool = False,
) -> InlineKeyboardMarkup:
    """Клавиатура управления редактором дорожной карты."""
    builder = InlineKeyboardBuilder()

    if changes:
        builder.button(
            text='💾 Сохранить изменения',
            callback_data=ManagerRoadmapCallback(
                roadmap_id=roadmap.id,
                intern_id=intern_id,
                action='save_edited_roadmap',
            ),
        )

    builder.button(
        text='Изменить название',
        callback_data=ManagerRoadmapCallback(
            roadmap_id=roadmap.id,
            intern_id=intern_id,
            action='edit_roadmap_name',
        ),
    )

    builder.button(
        text='Изменить описание',
        callback_data=ManagerRoadmapCallback(
            roadmap_id=roadmap.id,
            intern_id=intern_id,
            action='edit_roadmap_description',
        ),
    )

    builder.button(
        text='Редактор контрольных точек',
        callback_data=ManagerRoadmapCallback(
            roadmap_id=roadmap.id,
            intern_id=intern_id,
            action='referencepoints_selector',
        ),
    )

    if changes:
        back_button_callback = ManagerStartCallback(
            action='show_unsaved_alert',
        )
    else:
        back_button_callback = ManagerInternCallback(
            intern_id=intern_id,
            action='manager_intern_actions',
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


def roadmap_editor_cancel_keyboard(
    intern_id: int,


) -> InlineKeyboardMarkup:
    """Клавиатура отмены редактирования."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='❌ Отменить',
        callback_data=ManagerInternCallback(
            action='manager_intern_edit_roadmap',
            intern_id=intern_id,
        ),
    )

    builder.adjust(1)
    return builder.as_markup()
