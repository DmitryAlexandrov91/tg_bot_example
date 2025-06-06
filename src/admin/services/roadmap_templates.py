from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from admin.keyboards import build_confirm_keyboard_for
from admin.states.roadmap_templates import RoadmapTemplateForm


async def show_summary_and_confirm_roadmap_template(
    message: Message,
    state: FSMContext,
) -> None:
    """Отображает введённые данные и запрашивает подтверждение."""
    data = await state.get_data()
    await message.answer(
        'Проверьте данные:\n\n'
        f'1. Название: {data["name"]}\n'
        f'2. Описание: {data["description"]}\n\n'
        'Создать шаблон дорожной карты или отредактировать поле?.',
        reply_markup=build_confirm_keyboard_for(prefix='create_temp'),
    )
    await state.set_state(RoadmapTemplateForm.confirm)


async def maybe_confirm_edit_roadmap_template(
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
        await show_summary_and_confirm_roadmap_template(message, state)
        return True
    return False
