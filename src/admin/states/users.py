from aiogram.fsm.state import State, StatesGroup


class UserForm(StatesGroup):
    """FSM-состояния для создания пользователя."""

    first_name = State()
    last_name = State()
    patronymic = State()
    role = State()
    tg_id = State()
    email = State()
    phone_number = State()
    timezone = State()
    additional_info = State()
    confirm = State()


class EditUserForm(StatesGroup):
    """FSM-состояния для редактирования пользователя."""

    user_id = State()
    field = State()
    value = State()


class InvitationForm(StatesGroup):
    """FSM-состояния для создания ссылки-приглашения."""

    user_id = State()
    created_at = State()
    expires_at = State()
    link_token = State()
