from typing import Any, Union

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from admin.keyboards import build_confirm_keyboard_for
from admin.states.restaurants import RestaurantForm


async def show_summary_and_confirm_restaurant(
    message: Message,
    state: FSMContext,
) -> None:
    """Отображает введённые данные и запрашивает подтверждение."""
    data = await state.get_data()
    await message.answer(
        f'Проверьте данные:\n\n'
        f'1. Название: {data["name"]}\n'
        f'2. Полный адрес: {data["full_address"]}\n'
        f'3. Короткий адрес: {data["short_address"]}\n'
        f'4. Контакты: {data["contact_information"]}\n\n'
        'Создать ресторан или отредактировать поле?.',
        reply_markup=build_confirm_keyboard_for(prefix='create_rest'),
    )
    await state.set_state(RestaurantForm.confirm)


async def maybe_confirm_edit_restaurant(
    message: Message,
    state: FSMContext,
) -> bool:
    """Проверка флага редактирования.

    Если мы в режиме редактирования (editing==True),
    сбрасывает флаг и показывает сводку,
    возвращает True (чтобы хэндлер сразу завершился).
    """
    data = await state.get_data()
    if data.get('editing'):
        await state.update_data(editing=False)
        await show_summary_and_confirm_restaurant(message, state)
        return True
    return False


async def update_restaurant_state(
    state: FSMContext,
    key: str,
    value: Any,
    next_state: Union[str, FSMContext],
    message: Message,
    prompt: str,
) -> bool:
    """Общая логика FSM шагов."""
    await state.update_data({key: value})
    if await maybe_confirm_edit_restaurant(message, state):
        return True
    await message.answer(prompt)
    await state.set_state(next_state)
    return False
