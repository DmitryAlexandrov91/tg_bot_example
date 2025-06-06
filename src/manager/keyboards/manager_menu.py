from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from manager.callbacks import ManagerStartCallback


def get_manager_start_menu() -> InlineKeyboardMarkup:
    """Стартовая клавиатура Менеджера."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Управление шаблонами дорожных карт',
        callback_data=ManagerStartCallback(
            action='manager_templateroadmaps',
        ),
    )

    builder.button(
        text='Управление стажёрами',
        callback_data=ManagerStartCallback(
            action='manager_interns',
        ),
    )

    builder.adjust(1)
    return builder.as_markup()
