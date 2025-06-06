"""Скрипт для создание администратора."""

import asyncio

from config import settings
from crud.users import user_crud
from engine import session_maker
from models.constants import UserRole

obj = {
    'first_name': settings.FIRST_NAME,
    'last_name': settings.LAST_NAME,
    'patronymic': settings.PATRONYMIC,
    'role': UserRole.ADMIN,
    'tg_id': settings.TG_ID,
    'email': settings.EMAIL,
    'phone_number': settings.PHONE_NUMBER,
}


async def create_admin() -> None:
    """Создаёт администратора с данными из config."""
    async with session_maker() as session:
        await user_crud.create(session=session, obj_in=obj)


if __name__ == '__main__':
    asyncio.run(create_admin())
