from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from engine import session_maker


class DataBaseSession(BaseMiddleware):
    """Middleware, создающий асинхронную сессию для подключения к бд."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Метод для добавления сессий в существующие хендлеры."""
        async with session_maker() as session:
            try:
                data['session'] = session
                result = await handler(event, data)
                await session.commit()
                return result

            except Exception as e:
                await session.rollback()
                raise e

            finally:
                await session.close()
