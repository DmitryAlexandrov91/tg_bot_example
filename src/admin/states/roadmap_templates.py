from aiogram.fsm.state import State, StatesGroup


class RoadmapTemplateForm(StatesGroup):
    """FSM-состояния для создания шаблона дорожной карты."""

    name = State()
    description = State()
    confirm = State()


class RoadmapTemplateEditForm(StatesGroup):
    """FSM-состояния для редактирования шаблона дорожной карты."""

    template_roadmap_id = State()
    field = State()
    value = State()
