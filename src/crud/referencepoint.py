from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.base import CRUDBase
from models.models import ReferencePoint, RoadMap, Test, UserRoadMap


class ReferencePointCRUD(CRUDBase):
    """CRUD модели referencepoint."""

    async def get_current_user_point(
        self, intern_id: int, session: AsyncSession,
    ) -> list[RoadMap]:
        """Возвращает все контрольные точки активных дорожных карт стажера."""
        roadmaps_id = (
            await session.execute(select(UserRoadMap.roadmap_id).where(
                UserRoadMap.user_id == intern_id,
            ))
        ).scalars().all()
        return (
            await session.execute(select(self.model).where(
                self.model.id.in_(roadmaps_id),
            ))
        ).scalars().all()

    async def get_reference_point_by_id(
        self, point_id: int, session: AsyncSession,
    ) -> ReferencePoint:
        """Возвращает контрольную точку по ее ID со связанными сущностями."""
        return (
            await session.execute(
                select(ReferencePoint)
                .options(
                    selectinload(ReferencePoint.notification),
                    selectinload(ReferencePoint.feedback_request),
                    selectinload(ReferencePoint.test).selectinload(
                        Test.questions,
                    ),
                )
                .where(ReferencePoint.id == point_id),
            )
        ).scalars().one()


referencepoint_crud = ReferencePointCRUD(ReferencePoint)

roadmap_crud = None
