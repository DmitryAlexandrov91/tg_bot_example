from aiogram.fsm.state import State, StatesGroup


class AssignRoadmapStates(StatesGroup):
    """Состояние для назначения Дорожной карты Стажёру."""

    processing_point = State()
    waiting_for_check_datetime = State()
    waiting_for_reminder_days = State()
    waiting_for_trigger_time = State()


class EditRoadmapStates(StatesGroup):
    """Состояния для редактирования Дорожной карты."""

    selecting_action = State()
    editing_name = State()
    editing_description = State()


class EditReferencepointStates(StatesGroup):
    """Состояния для редактирования Контрольных точек."""

    editing_name = State()
    editing_notification_text = State()
    editing_trigger_datetime = State()
    editing_check_datetime = State()
    editing_reminder = State()


class EditTemplateRoadmapStates(StatesGroup):
    """Состояния для редактирования Шаблона Дорожной карты."""

    selecting_action = State()
    editing_name = State()
    editing_description = State()
    editing_status = State()


class EditTemplateReferencepointStates(StatesGroup):
    """Состояния для редактирования Шаблона контрольной точки."""

    selecting_action = State()
    editing_name = State()
    editing_notification_text = State()
    editing_point_type = State()
    editing_quiz = State()


class ManagerMessage(StatesGroup):
    """Состояние для получения сообщения от менеджера."""

    intern_tg_id = State()
    intern_id = State()
    intern_first_name = State()
    intern_last_name = State()
    message = State()
