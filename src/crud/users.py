from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.models import User


class UserCRUD(CRUDBase):
    """CRUD модели user."""

    async def get_user_by_tg_id(
        self,
        session: AsyncSession,
        tg_id: int,
    ) -> User | None:
        """Возвращает юзера по его tg_id."""
        stmt = select(self.model).where(self.model.tg_id == tg_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_managers_interns(
        self, manager_id: int, session: AsyncSession,
    ) -> list[User]:
        """Метод возвращает всех стажеров, определенного менеджера."""
        return (
            await session.execute(select(self.model).where(
                self.model.manager_id == manager_id,
            ))
        ).scalars().all()

    async def get_tgid_by_id(
        self,
        user_id: int,
        session: AsyncSession,
    ) -> Optional[int]:
        """Метод возвращает tg id user по его id в базе данных."""
        return (
            await session.execute(select(self.model.tg_id).where(
                self.model.id == user_id,
            ))
        ).scalars().first()

    async def end_education_intern(
        self,
        intern_id: int,
        session: AsyncSession,
    ) -> User:
        """Метод досрочно завершает обучение стажера."""
        intern = await self.get(intern_id, session)
        intern.is_education_complete = True
        session.add(intern)
        await session.commit()
        await session.refresh(intern)
        return intern

    async def ban_user(
        self,
        intern_id: int,
        session: AsyncSession,
    ) -> User:
        """Метод блокирует стажера."""
        intern = await self.get(intern_id, session)
        intern.is_active = False
        session.add(intern)
        await session.commit()
        await session.refresh(intern)
        return intern

    async def get_manager_id(
            self,
            user_tg_id: int,
            session: AsyncSession) -> int | None:
        """Получить Telegram ID менеджера по Telegram ID стажёра."""
        result = await session.execute(
            select(self.model.manager_id)
            .where(self.model.tg_id == user_tg_id),
        )
        manager_id = result.scalar_one_or_none()
        if manager_id is None:
            return None
        result = await session.execute(
            select(self.model.tg_id).where(self.model.id == manager_id),
        )
        return result.scalar_one_or_none()


user_crud = UserCRUD(User)
