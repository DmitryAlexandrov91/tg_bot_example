from typing import Any, Dict, Generic, Never, Optional, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.base import BaseModel
from models.models import User

T = TypeVar('T', bound=BaseModel)


class CRUDBase:
    """Базовый класс методов CRUD."""

    def __init__(self, model: Generic[T]) -> None:
        """Инициализирует переменные класса CRUDBase."""
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
        *,
        load_relations: bool = False,
        relations_to_upload: Optional[list] = None,
    ) -> Optional[T] | None:
        """Метод возвращает объект модели для чтения.

        load_relations = True загружает связанные объекты.
        """
        operation = select(self.model).where(self.model.id == obj_id)

        if load_relations:
            operation = operation.options(selectinload('*'))

        if relations_to_upload:
            for relation in relations_to_upload:
                operation = operation.options(selectinload(relation))

        return (
            (
                await session.execute(
                    operation,
                )
            )
            .scalars()
            .first()
        )

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        options: list[Any] = None,
    ) -> list | Sequence[Never]:
        """Возвращает все объекты модели с возможностью подгрузки связей."""
        stmt = select(self.model)
        if options is not None:
            stmt = stmt.options(*options)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_multi_filtered(
        self,
        session: AsyncSession,
        *filters: Any,
    ) -> list[T]:
        """Метод возвращает все объекты модели с фильтрами."""
        return list(
            (
                await session.execute(
                    select(self.model).where(*filters),
                )
            )
            .scalars()
            .all(),
        )

    async def create(
        self,
        obj_in: Dict[str, Any],
        session: AsyncSession,
        user: Optional[User] = None,
    ) -> T:
        """Метод создает и возвращает новый объект модели."""
        if user:
            obj_in['user_id'] = user.id
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: T,
        obj_in: Dict[str, Any],
        session: AsyncSession,
    ) -> T:
        """Метод обновляет и возвращает измененный объект модели."""
        for field in dict(
            (column, getattr(db_obj, column))
            for column in db_obj.__table__.columns.keys()
        ):
            if field in obj_in:
                setattr(db_obj, field, obj_in[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: T, session: AsyncSession) -> T:
        """Метод удаляет и возвращает удаленный объект модели."""
        await session.delete(db_obj)
        await session.commit()
        return db_obj
