# =========================
# Общие клавиатуры
# =========================
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from models.models import Restaurant, TemplateRoadMap, User


def build_confirm_keyboard_for(prefix: str) -> InlineKeyboardMarkup:
    """Клавитура подтверждения."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Создать',
                    callback_data=f'{prefix}:confirm_yes',
                ),
                InlineKeyboardButton(
                    text='Редактировать поле',
                    callback_data=f'{prefix}:redact_field',
                ),
            ],
        ],
    )


role_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='ADMIN', callback_data='role:ADMIN'),
            InlineKeyboardButton(text='MANAGER', callback_data='role:MANAGER'),
            InlineKeyboardButton(text='USER', callback_data='role:USER'),
        ],
    ],
)


point_type_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Тест',
                callback_data='point_type:Test',
            ),
            InlineKeyboardButton(
                text='Уведомление',
                callback_data='point_type:Notification',
            ),
            InlineKeyboardButton(
                text='Обратная связь',
                callback_data='point_type:feedback_request',
            ),
        ],
    ],
)


timezone_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text=tz, callback_data=f'timezone:{tz}')]
        for tz in [
            'Europe/Kaliningrad',
            'Europe/Moscow',
            'Europe/Samara',
            'Asia/Yekaterinburg',
            'Asia/Omsk',
            'Asia/Krasnoyarsk',
            'Asia/Irkutsk',
            'Asia/Yakutsk',
            'Asia/Vladivostok',
            'Asia/Kamchatka',
        ]
    ],
)

# =========================
# Админская клавиатура
# =========================

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Создать пользователя'),
            KeyboardButton(text='Редактировать пользователя'),
            KeyboardButton(text='Заблокировать пользователя'),
        ],
        [
            KeyboardButton(text='Привязать пользователя к ресторану'),
            KeyboardButton(text='Сгенерировать приглашение'),
        ],
        [
            KeyboardButton(text='Создать ресторан'),
            KeyboardButton(text='Редактировать ресторан'),
            KeyboardButton(text='Заблокировать ресторан'),
        ],
        [
            KeyboardButton(text='Создать шаблон дорожной карты'),
            KeyboardButton(text='Редактировать шаблон дорожной карты'),
        ],
        [
            KeyboardButton(text='Заблокировать шаблон дорожной карты'),
            KeyboardButton(
                text='Привязать шаблон дорожной карты к ресторану',
            ),
        ],
        [
            KeyboardButton(text='Создать шаблон контрольной точки'),
        ],
        [
            KeyboardButton(text='Отмена'),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# =========================
# Работа с пользователями
# =========================


fields_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f'edit_field:{field_key}',
            ),
        ]
        for field_key, label in [
            ('first_name', 'Имя'),
            ('last_name', 'Фамилия'),
            ('patronymic', 'Отчество'),
            ('role', 'Роль'),
            ('tg_id', 'TG_ID'),
            ('email', 'Email'),
            ('phone_number', 'Телефон'),
            ('timezone', 'Часовой пояс'),
            ('additional_info', 'Доп. инфо'),
        ]
    ],
)


fields_keyboard_edit = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f'edit_fields_user_before:{field_key}',
            ),
        ]
        for field_key, label in [
            ('first_name', 'Имя'),
            ('last_name', 'Фамилия'),
            ('patronymic', 'Отчество'),
            ('role', 'Роль'),
            ('tg_id', 'TG_ID'),
            ('email', 'Email'),
            ('phone_number', 'Телефон'),
            ('timezone', 'Часовой пояс'),
            ('additional_info', 'Доп. инфо'),
        ]
    ],
)


def build_user_select_keyboard(
    users: list[User],
    prefix: str,
) -> InlineKeyboardMarkup:
    """Клавиатура выбора пользователя."""
    buttons = [
        [
            InlineKeyboardButton(
                text=(
                    f'{user.first_name} {user.last_name} | '
                    f'TG: {user.tg_id} | '
                    f'Ресторан: '
                    f'{user.restaurant.name if user.restaurant else "–––"}'
                ),
                callback_data=f'{prefix}:{user.tg_id}',
            ),
        ]
        for user in users
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_user_id_select_keyboard(
    users: list[User],
    prefix: str,
) -> InlineKeyboardMarkup:
    """Клавиатура выбора пользователя. Возвращает id."""
    buttons = [
        [
            InlineKeyboardButton(
                text=(f'{user.first_name} {user.last_name}'),
                callback_data=f'{prefix}:{user.id}',
            ),
        ]
        for user in users
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_confirm_keyboard(
    entity_id: int,
    entity: str,
) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения блокировки пользователя."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Да',
                    callback_data=f'confirm_block_{entity}:{entity_id}',
                ),
                InlineKeyboardButton(
                    text='Нет',
                    callback_data=f'cancel_block_{entity}',
                ),
            ],
        ],
    )


# =========================
# Работа с ресторанами
# =========================


edit_fields_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f'edit_field_rest_before:{field_key}',
            ),
        ]
        for field_key, label in [
            ('name', 'Название'),
            ('full_address', 'Полный адрес'),
            ('short_address', 'Короткий адрес'),
            ('contact_information', 'Контакты'),
        ]
    ],
)


fields_rest_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f'edit_rest_field:{field_key}',
            ),
        ]
        for field_key, label in [
            ('name', 'Название'),
            ('full_address', 'Полный адрес'),
            ('short_address', 'Короткий адрес'),
            ('contact_information', 'Контактная информация'),
        ]
    ],
)


def build_restaurant_select_keyboard(
    restaurants: list[Restaurant],
    prefix: str,
) -> InlineKeyboardMarkup:
    """Клавиатура выбора ресторана."""
    buttons = [
        [
            InlineKeyboardButton(
                text=restaurant.name,
                callback_data=f'{prefix}:{restaurant.id}',
            ),
        ]
        for restaurant in restaurants
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================
# Работа с шаблонами дорожной карты
# =========================


roadmap_edit_fields_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f'edit_field_roadmap_before:{field_key}',
            ),
        ]
        for field_key, label in [
            ('name', 'Название'),
            ('description', 'Описание'),
        ]
    ],
)


fields_template_roadmap_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f'edit_roadmap_template_field:{field_key}',
            ),
        ]
        for field_key, label in [
            ('name', 'Название'),
            ('description', 'Описание'),
        ]
    ],
)


def build_roadmap_template_select_keyboard(
    roadmap_templates: list[TemplateRoadMap],
    prefix: str,
) -> InlineKeyboardMarkup:
    """Клавиатура выбора шаблона дорожной карты."""
    buttons = [
        [
            InlineKeyboardButton(
                text=template.name,
                callback_data=f'{prefix}:{template.id}',
            ),
        ]
        for template in roadmap_templates
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================
# Приглашение
# =========================


def invite_keyboard(code: str, bot_username: str) -> InlineKeyboardMarkup:
    """Кнопка для приглашения."""
    link = f'https://t.me/{bot_username}?start={code}'
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Отправить приглашение', url=link))
    return keyboard
