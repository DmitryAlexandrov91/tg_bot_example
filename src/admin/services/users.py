from typing import Any, Optional, Union

from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
)

from admin.keyboards import build_confirm_keyboard_for
from admin.states.users import UserForm


async def show_summary_and_confirm(
    message: Message,
    state: FSMContext,
) -> None:
    """Отображает введённые данные и запрашивает подтверждение."""
    data = await state.get_data()
    await message.answer(
        f'Проверьте данные:\n\n'
        f'1. Имя: {data["first_name"]}\n'
        f'2. Фамилия: {data["last_name"]}\n'
        f'3. Отчество: {data["patronymic"] or "—"}\n'
        f'4. Роль: {data["role"]}\n'
        f'5. TG ID: {data["tg_id"]}\n'
        f'6. Email: {data["email"]}\n'
        f'7. Телефон: {data["phone_number"]}\n'
        f'8. Часовой пояс: {data["timezone"]}\n'
        f'9. Доп. информация: {data["additional_info"] or "—"}\n'
        'Создать пользователя или отредактировать поле?',
        reply_markup=build_confirm_keyboard_for(prefix='create_user'),
    )
    await state.set_state(UserForm.confirm)


async def maybe_confirm_edit(message: Message, state: FSMContext) -> bool:
    """Проверка флага редактирования.

    Если мы в режиме редактирования (editing==True),
    сбрасывает флаг и показывает сводку,
    возвращает True (чтобы хэндлер сразу завершился).
    """
    data = await state.get_data()
    if data.get('editing'):
        await state.update_data(editing=False)
        await show_summary_and_confirm(message, state)
        return True
    return False


async def update_user_state(
    state: FSMContext,
    key: str,
    value: Any,
    next_state: Union[str, FSMContext],
    message: Message,
    prompt: str,
    reply_markup: Optional[ReplyKeyboardMarkup | InlineKeyboardMarkup] = None,
) -> bool:
    """Общая логика FSM шагов."""
    await state.update_data({key: value})
    if await maybe_confirm_edit(message, state):
        return True
    await message.answer(prompt, reply_markup=reply_markup)
    await state.set_state(next_state)
    return False
