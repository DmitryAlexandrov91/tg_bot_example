from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from crud.users import user_crud
from models.constants import UserRole


class RoleCheckMiddleware(BaseMiddleware):
    """Middleware для проверки ролей пользователей."""

    def __init__(
        self,
        allowed_roles: Optional[list[UserRole]] = None,
    ) -> None:
        """Инициализирует RoleCheckMiddleware класс."""
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Метод для добавления проверки идентификации."""
        session = data['session']

        user = await user_crud.get_user_by_tg_id(
            session=session,
            tg_id=event.from_user.id,
        )

        if user is None:
            raise PermissionError('Пользователь не найден в системе')

        if self.allowed_roles and user.role not in self.allowed_roles:
            raise PermissionError(
                f'Доступ запрещен. Требуемые роли: {self.allowed_roles}',
            )

        data['user'] = user

        return await handler(event, data)
