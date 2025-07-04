from enum import StrEnum
from string import ascii_lowercase, ascii_uppercase, digits


class UserRole(StrEnum):
    """Роли пользователей."""

    USER = 'USER'
    MANAGER = 'MANAGER'
    ADMIN = 'ADMIN'


class ReferencePointType(StrEnum):
    """Типы контрольных точек."""

    NOTIFICATION = 'NOTIFICATION'
    TEST = 'TEST'
    FEEDBACK_REQUEST = 'FEEDBACK_REQUEST'


ACCEPTABLE_SYMBOLS = ascii_lowercase + ascii_uppercase + digits

ATTEMPS_COUNT = 100

TOKEN_LENGTH = 10

TEST_TIME_RESPOND = 20
TEST_MAX_ANSWERS_COUNT = 5
MAX_LEN_NAME_ROADMAP = 100
MAX_LEN_NAME_REFERENCEPOINT = 100
MAX_LEN_NAME_TEST = 100
MAX_LEN_EMAIL = 100
MAX_LEN_RESTAURANT_NAME = 100
MAX_LEN_PHONE_NUMBER = 20
MAX_LEN_TIMEZONE = 35
MAX_LEN_SHORT_ADDRESS_RESTAURANT = 100
MAX_LEN_CONTACT_INFO_RESTAURANT = 100
MAX_LEN_FIRST_NAME = 50
MAX_LEN_LAST_NAME = 50
MAX_LEN_PATRONYMIC = 50
MOSCOW_TIMEZONE = 'Europe/Moscow'
REMINDER_DAYS_BEFORE = 0
