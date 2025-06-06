from aiogram.fsm.state import State, StatesGroup


class RestaurantForm(StatesGroup):
    """FSM-состояния для создания ресторана."""

    name = State()
    full_address = State()
    short_address = State()
    contact_information = State()
    confirm = State()


class EditRestaurantForm(StatesGroup):
    """FSM-состояния для редактирования ресторана."""

    field = State()
    value = State()
