from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

intern_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Посмотреть статус дорожной карты')],
        [KeyboardButton(text='Посмотреть текущую контрольную точку')],
        [KeyboardButton(text='Отправить сообщение менеджеру')],
        [KeyboardButton(text='Дополнительно')],

    ],
    resize_keyboard=True,
)

additionally_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Запрос на досрочное прекращение стажировки')],
        [KeyboardButton(text='Вернуться назад')],
    ],
    resize_keyboard=True,
)
