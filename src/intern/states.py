from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup


class SelectInternCallback(CallbackData, prefix='select_intern'):
    """Состояние для ДОПИСАТЬ."""

    intern_tg_id: int


class TerminationRoadMap(StatesGroup):
    """Состояние для причины прекращения прохождения дорожной карты."""

    waiting_for_reason = State()


class InternReply(StatesGroup):
    """Состояние для ответа на сообщение менеджера."""

    entering_message_to_manager = State()


class ManagerReply(StatesGroup):
    """Состояние для ответа на сообщение стажера."""

    entering_reply_text = State()


class FeedbackStates(StatesGroup):
    """Состояние для ответа на обратную связь."""

    waiting_for_feedback = State()
