from sqlalchemy import Identity, Integer
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
)


class BaseModel(DeclarativeBase):
    """Базовый класс для всех моделей."""

    @declared_attr.directive
    def __tablename__(self) -> str:
        return self.__name__.lower()

    id: Mapped[int] = mapped_column(
            Integer,
            Identity(always=True),
            primary_key=True,
        )
