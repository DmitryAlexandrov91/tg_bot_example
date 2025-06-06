from typing import Any, Optional, Union

from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
)

# async def show_summary_and_confirm(
#     message: Message,
#     state: FSMContext,
# ) -> None:
#     """Отображает введённые данные и запрашивает подтверждение."""
#     data = await state.get_data()
#     await message.answer(
#         f'Проверьте данные:\n\n'
#         f'1. Название: {data["name"]}\n'
#         f'2. Тип контрольной точки: {data["point_type"]}\n'
#         f'3. Отчество: {data["patronymic"]}\n'
#         f'4. Роль: {data["role"]}\n'
#         f'5. TG ID: {data["tg_id"]}\n'
#         f'6. Email: {data["email"]}\n'
#         f'7. Телефон: {data["phone_number"]}\n'
#         f'8. Часовой пояс: {data["timezone"]}\n'
#         f'9. Доп. информация: {data["additional_info"] or "—"}\n'
#         'Создать пользователя или отредактировать поле?',
#         reply_markup=build_confirm_keyboard_for(prefix='create_user'),
#     )
#     await state.set_state(UserForm.confirm)


async def update_ref_point_state(
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
    await message.answer(prompt, reply_markup=reply_markup)
    await state.set_state(next_state)
    return False
