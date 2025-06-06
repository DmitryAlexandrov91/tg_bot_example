import re


def is_valid_email(email: str) -> bool:
    """Проверяет, соответствует ли строка формату email."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def is_valid_phone_number(phone: str) -> bool:
    """Проверяет, что номер телефона соответствует формату.

    - начинается с + или цифры
    - состоит из 10–15 цифр
    - допускается только один '+' в начале
    """
    phone = phone.strip()
    return bool(re.fullmatch(r'\+?\d{10,15}', phone))
