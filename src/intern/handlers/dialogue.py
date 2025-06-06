from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from crud.users import user_crud
from intern.states import InternReply, ManagerReply
from intern.utils import save_message

dialogue_router = Router()


@dialogue_router.message(F.text == 'Отправить сообщение менеджеру')
async def start_send_message_to_manager(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Начинаем процесс отправки сообщения менеджеру."""
    sender_id = message.from_user.id
    receiver_id = await user_crud.get_manager_id(sender_id, session)
    if receiver_id is None:
        await message.answer('❗️Вы не прикреплены к менеджеру.')
        await state.clear()
        return
    await state.set_state(InternReply.entering_message_to_manager)
    await message.answer('Введите сообщение для отправки менеджеру:')


@dialogue_router.message(InternReply.entering_message_to_manager)
async def send_message_to_manager(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Отправляет сообщение менеджеру."""
    sender_id = message.from_user.id
    receiver_id = await user_crud.get_manager_id(sender_id, session)
    text = message.text
    reply_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✉️ Ответить',
                    callback_data=f'reply_to_intern:{sender_id}',
                ),
            ],
        ],
    )
    await message.bot.send_message(
        chat_id=receiver_id,
        text=f'💬 Новое сообщение от стажёра:\n\n{text}',
        reply_markup=reply_button,
    )
    await save_message(sender_id, receiver_id, text, session)
    await message.answer('Сообщение менеджеру отправлено.')
    await state.clear()


@dialogue_router.callback_query(F.data.startswith('reply_to_intern'))
async def handle_reply_to_intern(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Начало ввода ответа менеджера стажёру."""
    await callback.answer()
    intern_id = int(callback.data.split(':')[1])
    await state.update_data(intern_id=intern_id)
    await state.set_state(ManagerReply.entering_reply_text)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer('Введите ответ стажёру:')


@dialogue_router.message(ManagerReply.entering_reply_text)
async def handle_manager_reply(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка текста ответа менеджера стажёру."""
    data = await state.get_data()
    intern_id = data.get('intern_id')
    if not intern_id:
        await message.answer('Ошибка: не найден ID стажёра.')
        await state.clear()
        return
    reply_text = message.text
    sender_id = message.from_user.id
    reply_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✉️ Ответить',
                    callback_data=f'reply_to_manager:{sender_id}',
                ),
            ],
        ],
    )
    await message.bot.send_message(
        chat_id=intern_id,
        text=f'💬 Ответ от менеджера:\n\n{reply_text}',
        reply_markup=reply_button,
    )
    await save_message(sender_id, intern_id, reply_text, session)
    await message.answer('Ответ отправлен стажёру.')
    await state.clear()


@dialogue_router.callback_query(F.data.startswith('reply_to_manager'))
async def handle_reply_to_manager(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Начало ввода ответа стажёра менеджеру."""
    await callback.answer()
    manager_id = int(callback.data.split(':')[1])
    await state.update_data(manager_id=manager_id)
    await state.set_state(InternReply.entering_message_to_manager)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer('Введите ответ менеджеру:')


@dialogue_router.message(InternReply.entering_message_to_manager)
async def handle_intern_reply(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка текста ответа стажёра менеджеру."""
    data = await state.get_data()
    manager_id = data.get('manager_id')
    if not manager_id:
        await message.answer('Ошибка: не найден ID менеджера.')
        await state.clear()
        return
    reply_text = message.text
    sender_id = message.from_user.id
    reply_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✉️ Ответить',
                    callback_data=f'reply_to_manager:{sender_id}',
                ),
            ],
        ],
    )
    await message.bot.send_message(
        chat_id=manager_id,
        text=f'💬 Ответ от стажёра:\n\n{reply_text}',
        reply_markup=reply_button,
    )
    await save_message(sender_id, manager_id, reply_text, session)
    await message.answer('Ответ отправлен менеджеру.')
    await state.clear()
