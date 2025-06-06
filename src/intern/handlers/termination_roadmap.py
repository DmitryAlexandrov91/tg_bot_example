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
from intern.keyboards import additionally_keyboard, intern_keyboard
from intern.states import TerminationRoadMap

term_roadmap_router = Router()


@term_roadmap_router.message(F.text == 'Дополнительно')
async def show_additional_menu(message: Message) -> None:
    """Отображение меню после нажатия на кнопку 'Дополнительно'."""
    await message.answer(
        'Выберите действие:',
        reply_markup=additionally_keyboard,
    )


@term_roadmap_router.message(F.text == 'Вернуться назад')
async def back_to_main_menu(message: Message) -> None:
    """Обработчик нажатия на кнопку 'Вернуться назад'."""
    await message.answer(
        'Главное меню:',
        reply_markup=intern_keyboard,
    )


@term_roadmap_router.message(
    F.text == 'Запрос на досрочное прекращение стажировки',
)
async def termination_of_the_roadmap(
    message: Message,
    state: FSMContext,
) -> None:
    """Досрочное прекращение выполнения дорожной карты с указанием причины."""
    await message.answer(
        '❗Пожалуйста, опишите причину по которой '
        'хотите прекратить выполнения дорожной карты.',
    )
    await state.set_state(TerminationRoadMap.waiting_for_reason)


@term_roadmap_router.message(TerminationRoadMap.waiting_for_reason)
async def receive_reason(message: Message, state: FSMContext) -> None:
    """Обрбатываем введенную пользователем причину."""
    reason = message.text
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='✅ Отправить',
                    callback_data='send_reason_msg',
                ),
                InlineKeyboardButton(
                    text='❌ Отмена',
                    callback_data='cancel_reason_msg',
                ),
            ],
        ],
    )
    await state.update_data(reason=reason)

    await message.answer(
        (
            f'Ваша причина: <b>{reason}</b>. Нажмите кнопку "Отправить" '
            f'для отправки сообщения менеджеру, либо нажмите кнопку "Отмена"'
        ),
        parse_mode='HTML',
        reply_markup=buttons,
    )


@term_roadmap_router.callback_query(F.data == 'send_reason_msg')
async def handle_send_reason(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработка нажатия кнопки отправки причины отмены."""
    await callback.answer()
    data = await state.get_data()
    reason = data.get('reason')
    intern_id = callback.from_user.id
    if not reason:
        await callback.message.answer(
            '❌ Причина не указана. Повторите ввод команды',
        )
        return
    manager_id = await user_crud.get_manager_id(intern_id, session)
    if manager_id is None:
        await callback.message.answer('⚠️ Не удалось найти менеджера.')
        return
    await callback.bot.send_message(
        chat_id=manager_id,
        text=(
            f'Стажёр @{callback.from_user.username} желает прекратить '
            f'прохождение дорожной карты по причине:\n<b>{reason}</b>'
        ),
        parse_mode='HTML',
    )
    await callback.message.edit_reply_markup(reply_markup=None)
    if callback.message:
        await callback.message.answer('✅ Причина отправлена менеджеру.')
    await state.clear()


@term_roadmap_router.callback_query(F.data == 'cancel_reason_msg')
async def handle_cancel_reason(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработка нажатия кнопки отмены отправки."""
    await callback.answer()
    if callback.message:
        await callback.message.edit_reply_markup(  # type: ignore
            reply_markup=None,
        )
        await callback.message.answer(
            '❌ Отмена отправки. Повторите ввод команды',
        )
    await state.clear()
