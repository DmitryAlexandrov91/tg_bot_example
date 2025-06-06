from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from manager.callbacks import (
    ManagerStartCallback,
    ManagerTemplateRoadmapCallback,
)
from manager.constants import (
    BACK,
    BACK_TO_MENU,
)
from models.models import TemplateRoadMap


def select_templateroadmap_keyboard(
        templateroadmaps: List[TemplateRoadMap],
) -> InlineKeyboardMarkup:
    """Клавиатура для выбора Шаблона дорожной карты."""
    builder = InlineKeyboardBuilder()

    for templateroadmap in templateroadmaps:
        builder.button(
            text=(
                f'{templateroadmap.name}'
                f'{" (🔒)" if templateroadmap.is_blocked else ""}'
            ),
            callback_data=ManagerTemplateRoadmapCallback(
                templateroadmap_id=templateroadmap.id,
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


def get_templateroadmap_menu_keyboard(
        templateroadmap: TemplateRoadMap,
) -> InlineKeyboardMarkup:
    """Клавиатура управления Шаблоном дорожной карты."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Редактировать Шаблон дорожной карты',
        callback_data=ManagerTemplateRoadmapCallback(
            templateroadmap_id=templateroadmap.id,
            action='edit_templateroadmap',
        ),
    )

    builder.button(
        text='Редактировать Шаблоны контрольных точек',
        callback_data=ManagerTemplateRoadmapCallback(
            templateroadmap_id=templateroadmap.id,
            action='templatereferencepoints_selector',
        ),
    )

    builder.button(
        text=BACK,
        callback_data=ManagerStartCallback(
            action='manager_templateroadmaps',
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


def get_templateroadmap_editor_menu_keyboard(
        templateroadmap: TemplateRoadMap,
        changes: bool = False,
) -> InlineKeyboardMarkup:
    """Клавиатура управления Редактором Дорожной карты."""
    builder = InlineKeyboardBuilder()

    if changes:
        builder.button(
            text='💾 Сохранить изменения',
            callback_data=ManagerTemplateRoadmapCallback(
                templateroadmap_id=templateroadmap.id,
                action='save_templateroadmap',
            ),
        )

    builder.button(
        text='Изменить название',
        callback_data=ManagerTemplateRoadmapCallback(
            templateroadmap_id=templateroadmap.id,
            action='edit_templateroadmap_name',
        ),
    )

    builder.button(
        text='Изменить описание',
        callback_data=ManagerTemplateRoadmapCallback(
            templateroadmap_id=templateroadmap.id,
            action='edit_templateroadmap_description',
        ),
    )

    block_status = (
        '🔓 Разблокировать' if templateroadmap.is_blocked
        else '🔒 Заблокировать'
    )
    builder.button(
        text=block_status,
        callback_data=ManagerTemplateRoadmapCallback(
            templateroadmap_id=templateroadmap.id,
            action='block_templateroadmap',
        ),
    )

    builder.button(
        text=BACK,
        callback_data=ManagerTemplateRoadmapCallback(
            templateroadmap_id=templateroadmap.id,
            action='show_unsaved_alert' if changes else 'select',
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


def templateroadmap_editor_cancel_keyboard(
        templateroadmap_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура управления Редактором Дорожной карты."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='❌ Отменить',
        callback_data=ManagerTemplateRoadmapCallback(
            templateroadmap_id=templateroadmap_id,
            action='edit_templateroadmap',
        ),
    )

    builder.adjust(1)
    return builder.as_markup()
