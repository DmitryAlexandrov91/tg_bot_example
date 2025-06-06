from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from crud.base import CRUDBase
from crud.users import user_crud
from models.models import RoadMap, User, UserRoadMap


class RoadmapCRUD(CRUDBase):
    """CRUD модели roadmap."""

    async def get_users_roadmap(
        self,
        intern_id: int,
        session: AsyncSession,
    ) -> RoadMap:
        """Возвращает дорожную карту стажера."""
        roadmap_id = (
            (
                await session.execute(
                    select(UserRoadMap.roadmap_id).where(
                        UserRoadMap.user_id == intern_id,
                    ),
                )
            )
            .scalars()
            .first()
        )
        return (
            (
                await session.execute(
                    select(self.model).where(
                        self.model.id == roadmap_id,
                    ),
                )
            )
            .scalars()
            .first()
        )

    async def get_user_id_by_roadmap_id(
        self,
        roadmap_id: int,
        session: AsyncSession,
    ) -> User:
        """Получить id юзера по id дорожной карты."""
        user_id = (
            (
                await session.execute(
                    select(UserRoadMap.user_id).where(
                        UserRoadMap.roadmap_id == roadmap_id,
                    ),
                )
            )
            .scalars()
            .first()
        )
        return await user_crud.get(user_id, session)

    async def get_user_roadmap(
        self,
        intern_id: int,
        session: AsyncSession,
    ) -> RoadMap | None:
        """Возвращает дорожную карту стажера."""
        result = await session.execute(
            select(UserRoadMap)
            .where(UserRoadMap.user_id == intern_id)
            .options(joinedload(UserRoadMap.roadmap)),
        )
        user_roadmap = result.scalars().first()
        return user_roadmap.roadmap if user_roadmap else None


roadmap_crud = RoadmapCRUD(RoadMap)
