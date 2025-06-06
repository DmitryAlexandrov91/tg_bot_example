from aiogram import F, Router
from aiogram.types import (
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from crud.roadmap import roadmap_crud
from models.models import User

status_point_router = Router()


@status_point_router.message(F.text == 'Посмотреть текущую контрольную точку')
async def current_checkpoint_handler(
    message: Message,
    session: AsyncSession,
    user: User,
) -> None:
    """Посмотреть статус контрольной точки."""
    roadmap = await roadmap_crud.get_user_roadmap(
        intern_id=user.id,
        session=session,
    )
    if not roadmap:
        await message.answer('У вас нет активной дорожной карты.')
        return

    for point in roadmap.reference_points:
        if not point.is_completed and point.check_datetime:
            await message.answer(
                text=(
                    f'🟡 <b>Текущий шаг</b>\n\n'
                    f'📌 <b>Дорожная карта:</b> {roadmap.name}\n'
                    f'🔖 <b>Название контрольной точки:</b> {point.name}\n'
                    f'📂 <b>Тип:</b> {point.point_type}\n'
                    f'📅 <b>Открыт с:</b> {point.trigger_datetime}\n'
                    f'⏳ <b>Статус:</b> В процессе\n'
                    f'💀 <b>Дедлайн:</b> {point.check_datetime}\n'
                ),
                parse_mode='HTML',
            )
            return
    await message.answer('На данный момент у вас нет активных шагов.')
