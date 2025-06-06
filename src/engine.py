from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings
from models import BaseModel

engine = create_async_engine(settings.database_url, echo=True)
session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db() -> None:
    """Метод для создания базы данных."""
    async with engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.create_all)


async def drop_db() -> None:
    """Метод для полного удаления базы данных."""
    async with engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.drop_all)
