from typing import Any, Awaitable, Callable, Dict

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from admin.keyboards import admin_keyboard


async def cancel_middleware(
    handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
    event: Message,
    data: Dict[str, Any],
) -> None:
    """Middleware для кнопки отмены."""
    text = (event.text or '').strip().lower()
    state: FSMContext = data['state']
    if text == 'отмена':
        await state.clear()
        await event.answer(
            'Действие отменено.',
            reply_markup=admin_keyboard,
        )
        return
    await handler(event, data)
