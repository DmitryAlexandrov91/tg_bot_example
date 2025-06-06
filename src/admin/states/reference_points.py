from aiogram.fsm.state import State, StatesGroup


class RefPointTemplateForm(StatesGroup):
    """FSM-состояния для создания контрольной точки."""

    name = State()
    point_type = State()
    order_execution = State()
    restaurant_id = State()
    templateroadmap_id = State()


# class RefPointTemplateEditForm(StatesGroup):
#     """FSM-состояния для редактирования шаблона дорожной карты."""
