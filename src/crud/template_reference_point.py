
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.models import TemplateReferencePoint


class CRUDTemplateRefferencePoint(CRUDBase):
    """Расширение базового CRUD для модели шаблона КТ."""

    async def get_ref_point_id_by_name(
        self,
        ref_point_name: str,
        session: AsyncSession,
    ) -> int:
        """Получение id шаблона КТ по по имени."""
        db_ref_point_id = await session.execute(
            select(TemplateReferencePoint.id).where(
                TemplateReferencePoint.name == ref_point_name,
            ),
        )
        return db_ref_point_id.scalars().first()


template_reference_point_crud = CRUDTemplateRefferencePoint(
    TemplateReferencePoint,
)
