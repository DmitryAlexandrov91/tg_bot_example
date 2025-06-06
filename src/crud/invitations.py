from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.models import InvitationLink


class InvitationCRUD(CRUDBase):
    """Расширение базового CRUD для модели приглашения."""

    async def get_by_token(
            self,
            link_token: str,
            session: AsyncSession,
    ) -> Optional[InvitationLink]:
        """Получение объекта ссылки-приглашения по токену."""
        db_invitation = await session.execute(
            select(InvitationLink).where(
                InvitationLink.link_token == link_token,
            ),
        )
        return db_invitation.scalars().first()


invite_crud = InvitationCRUD(InvitationLink)
