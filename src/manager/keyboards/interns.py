from typing import List

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from manager.callbacks import (
    ManagerInternCallback,
    ManagerStartCallback,
)
from manager.constants import (
    BACK,
    BACK_TO_MENU,
)
from models.models import User


def get_intern_keyboard(interns: List[User]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора Стажёра."""
    builder = InlineKeyboardBuilder()

    for intern in interns:
        builder.button(
            text=f'{intern.first_name} {intern.last_name}',
            callback_data=ManagerInternCallback(
                action='manager_intern_actions',
                intern_id=intern.id,
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


def get_interns_actions_keyboard(
    intern_id: int,
    intern_has_roadmap: bool = False,
) -> InlineKeyboardMarkup:
    """Клавиатура дальнейших действий со стажером."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Прогресс обучения',
        callback_data=ManagerInternCallback(
            action='manager_intern_education',
            intern_id=intern_id,
        ),
    )

    builder.button(
        text='Написать сообщение',
        callback_data=ManagerInternCallback(
            action='manager_intern_message',
            intern_id=intern_id,
        ),
    )

    if intern_has_roadmap:
        builder.button(
            text='Редактировать Дорожную карту',
            callback_data=ManagerInternCallback(
                action='manager_intern_edit_roadmap',
                intern_id=intern_id,
            ),
        )
    else:
        builder.button(
            text='Назначить Дорожную карту',
            callback_data=ManagerInternCallback(
                action='manager_intern_create_roadmap',
                intern_id=intern_id,
            ),
        )

    builder.button(
        text='Управление Стажёром',
        callback_data=ManagerInternCallback(
            action='manager_intern_menagement',
            intern_id=intern_id,
        ),
    )

    builder.button(
        text=BACK,
        callback_data=ManagerStartCallback(
            action='manager_interns',
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


def get_ban_or_end_education_keyboard(
    intern_id: int,
) -> InlineKeyboardMarkup:
    """Клавиатура для досрочного завершения обучения или бана стажера."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text='Заблокировать Стажёра',
        callback_data=ManagerInternCallback(
            action='ban_intern',
            intern_id=intern_id,
        ),
    )

    builder.button(
        text='Завершить обучение Стажёра',
        callback_data=ManagerInternCallback(
            action='end_education_intern',
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


def get_intern_answer_on_action(
    intern_id: int, name: str, surname: str,
) -> InlineKeyboardMarkup:
    """Клавиатура обработки действий со стажером."""
    builder = InlineKeyboardBuilder()

    builder.button(
        text=BACK,
        callback_data=ManagerInternCallback(
            action='manager_intern_actions',
            intern_id=intern_id,
            intern_first_name=name,
            intern_last_name=surname,
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
