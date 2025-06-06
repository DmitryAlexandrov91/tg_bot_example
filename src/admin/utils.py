from datetime import date, datetime
from random import sample
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from admin.constants import DT_FORMAT
from crud import invite_crud
from models.constants import ACCEPTABLE_SYMBOLS, TOKEN_LENGTH


async def check_unique_link_token(
    link_token: str,
    session: AsyncSession,
) -> bool:
    """Проверка уникальности токена ссылки-приглашения."""
    token = await invite_crud.get_by_token(link_token, session)
    if token:
        return False
    return True


async def get_unique_link_token(
    session: AsyncSession,
) -> str:
    """Генерация токена ссылки-приглашения."""
    token_unique = False
    while not token_unique:
        token = ''.join(sample(ACCEPTABLE_SYMBOLS, TOKEN_LENGTH))
        token_unique = await check_unique_link_token(token, session)
    return token


def json_serial(obj: datetime) -> Any:
    """Сериализация объекта datetime."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError('Type %s not serializable' % type(obj))


def json_deserial(obj: str) -> datetime:
    """Десериализация объекта json в datetime."""
    return datetime.strptime(obj[1:-1], DT_FORMAT)
