import json
from typing import List

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from crud.questions import question_crud
from crud.referencepoint import referencepoint_crud
from engine import session_maker
from intern.states import FeedbackStates
from intern.utils import (
    complete_ref_point,
)
from models import ReferencePoint, User

notifications_router = Router()


def extract_questions(quiz_items: List[str]) -> List[str]:
    """Возвращает список вопросов из списка json-строк."""
    return [json.loads(item)['text_question'] for item in quiz_items]


async def handle_reference_point_type(
    bot: Bot,
    reference_point: ReferencePoint,
    user: User,
    scheduler: AsyncIOScheduler,
) -> None:
    """Обрабатывает тип контрольной точки и отправляет уведомление."""
    user_id = user.tg_id
    async with session_maker() as session:
        if reference_point.point_type == 'TEST':
            # Отправка уведомления о тесте
            start_preview_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text='Начать прохождение теста',
                            callback_data=f'start_preview:{reference_point.id}',
                        ),
                    ],
                ],
            )
            await bot.send_message(
                user_id,
                'Вам необходимо пройти тест, вы готовы?',
                reply_markup=start_preview_keyboard,
            )

        elif reference_point.point_type == 'NOTIFICATION':
            await bot.send_message(
                user_id,
                (
                    '📩 Вам уведомление с контрольной точки:\n'
                    f'{reference_point.notification.text}'
                ),
            )
            await complete_ref_point(reference_point, scheduler, session)

        elif reference_point.point_type == 'FEEDBACK_REQUEST':
            feedback_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text='Ответить',
                            callback_data=f'feedback_keyboard:{reference_point.id}',
                        ),
                    ],
                ],
            )
            await bot.send_message(
                user_id,
                '📩 Пожалуйста, оставьте обратную связь.',
                reply_markup=feedback_keyboard,
            )
        else:
            raise ValueError('Похоже, контрольная точка не задана!')


@notifications_router.callback_query(F.data.startswith('feedback_keyboard:'))
async def handle_reply_to_intern(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Начало ввода ответа на обратную связь."""
    await callback.answer()
    ref_point_id = int(callback.data.split(':')[1])
    await state.update_data(ref_point_id=ref_point_id)
    await state.set_state(FeedbackStates.waiting_for_feedback)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer('Введите ответ:')


@notifications_router.message(FeedbackStates.waiting_for_feedback)
async def handle_reply_to_feedback(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработчик ответа на обратную связь."""
    data = await state.get_data()
    ref_point_id = data.get('ref_point_id')
    ref_point = await referencepoint_crud.get_reference_point_by_id(
        ref_point_id, session,
    )
    ref_point.feedback_request.user_answer = message.text
    session.add(ref_point.feedback_request)
    await session.commit()
    await complete_ref_point(ref_point, session)
    await message.answer('Ответ успешно сохранён!')
    await state.clear()


@notifications_router.callback_query(F.data.startswith('start_preview:'))
async def ask_confirmation(callback: CallbackQuery) -> None:
    """Обработчик начала."""
    reference_point_id = int(callback.data.split(":")[1])
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text='✅ Да',
                callback_data=f'handle_start_test:{reference_point_id}',
            ),
            InlineKeyboardButton(
                text='❌ Нет',
                callback_data='cancel_start',
            ),
        ],
    ])
    await callback.answer()
    await callback.message.answer(
        "Вы можете пройти тест только один раз. Начать?",
        reply_markup=confirm_keyboard,
    )


@notifications_router.callback_query(F.data == 'cancel_start')
async def handle_cancel_reason(callback: CallbackQuery) -> None:
    """Обработчик кнопки 'отмена'."""
    await callback.answer('❌ Отменено.')
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer('❌ Отмена действия.')


@notifications_router.callback_query(
    lambda c: c.data.startswith('handle_start_test:'),
)
async def handle_start(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Обработчик старта теста."""
    ref_point_id = int(callback.data.split(':')[1])
    ref_point = await referencepoint_crud.get_reference_point_by_id(
        ref_point_id, session,
    )
    questions = ref_point.test.questions

    for question in questions:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=answer, callback_data=f'answer:{question.id}:{i + 1}')]
            for i, answer in enumerate(question.answers)
        ])
        await callback.message.answer(
            f'{question.text_question}',
            reply_markup=keyboard,
        )


@notifications_router.callback_query(lambda c: c.data.startswith('answer:'))
async def handle_answer_callback(
    callback: CallbackQuery, session: AsyncSession,
) -> None:
    """Сохранение ответа на тест."""
    _, question_id_str, answer_index_str = callback.data.split(':')
    question_id = int(question_id_str)
    answer_index = int(answer_index_str)
    updated_question = await question_crud.update_user_answer(
        question_id, answer_index, session,
    )
    if updated_question:
        await callback.answer('Ответ сохранён ✅')
        await callback.message.edit_reply_markup(reply_markup=None)
    else:
        await callback.answer(
            'Ошибка при сохранении ответа ❌', show_alert=True,
        )
