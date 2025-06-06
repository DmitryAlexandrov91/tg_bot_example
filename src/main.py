import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.redis import RedisStorage

from admin.routers import admin_router
from common import start_help_router
from config import configure_logging, settings
from intern.handlers import intern_router
from manager.handlers import manager_router
from middlewares import DataBaseSession, RoleCheckMiddleware
from models.constants import UserRole

redis_storage_url = settings.redis_url

bot = Bot(settings.TOKEN)
dp = Dispatcher(storage=RedisStorage.from_url(url=redis_storage_url))

dp.update.middleware(DataBaseSession())

# общие команды только для зарегистрированных в БД пользователей
start_help_router.message.middleware(RoleCheckMiddleware())
start_help_router.callback_query.middleware(RoleCheckMiddleware())

# команды манагера только для манагера
manager_router.message.middleware(
    RoleCheckMiddleware(
        allowed_roles=[
            UserRole.MANAGER,
        ],
    ),
)
manager_router.callback_query.middleware(
    RoleCheckMiddleware(
        allowed_roles=[
            UserRole.MANAGER,
        ],
    ),
)

# команды юзера для юзера
intern_router.message.middleware(
    RoleCheckMiddleware(
        allowed_roles=[UserRole.USER, UserRole.MANAGER],
    ),
)
intern_router.callback_query.middleware(
    RoleCheckMiddleware(
        allowed_roles=[
            UserRole.USER, UserRole.MANAGER,
        ],
    ),
)


# команды админа только для админа
admin_router.message.middleware(
    RoleCheckMiddleware(allowed_roles=[UserRole.ADMIN]),
)
admin_router.callback_query.middleware(
    RoleCheckMiddleware(allowed_roles=[UserRole.ADMIN]),
)


dp.include_router(start_help_router)
dp.include_router(intern_router)
dp.include_router(manager_router)
dp.include_router(admin_router)


@dp.errors()
async def handle_unauthorized_error(
    event: types.ErrorEvent,
) -> bool:
    """Обработчик ошибок идентификации."""
    exception = event.exception

    if isinstance(exception, PermissionError):
        if event.update.message:
            await event.update.message.answer(
                '⛔️ Доступ запрещён',
            )
        return True

    configure_logging()
    logging.exception(
        f'\nВозникло исключение {str(exception)}\n',
        stack_info=True,
    )

    return False


async def main() -> None:
    """Главная функция создающая базу данных и асинхронные сессии.

    Запускает поллинг бота.
    """
    await dp.start_polling(bot)


# Временное решение: прерывание бота с Ctrl+C.
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен.')
