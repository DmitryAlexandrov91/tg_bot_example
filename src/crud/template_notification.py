from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.models import TemplateNotification


class CRUDTemplateNotification(CRUDBase):
    """Расширение базового CRUD для модели TemplateNotification."""

    async def get_by_referencepoint_id(
            self,
            referencepoint_id: int,
            session: AsyncSession,
    ) -> Optional[TemplateNotification]:
        """Получение TemplateNotification по ID связанной контрольной точки."""
        db_notification = await session.execute(
            select(TemplateNotification).where(
                TemplateNotification.referencepoint_id == referencepoint_id,
            ),
        )
        return db_notification.scalars().first()


template_notification_crud = CRUDTemplateNotification(TemplateNotification)
