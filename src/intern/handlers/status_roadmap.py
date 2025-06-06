from datetime import datetime

from aiogram import F, Router
from aiogram.types import (
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from crud.roadmap import roadmap_crud
from models.models import User

status_roadmap_router = Router()


@status_roadmap_router.message(F.text == 'Посмотреть статус дорожной карты')
async def status_roadmap_handler(
    message: Message,
    session: AsyncSession,
    user: User,
) -> None:
    """Информирование стажера о статусе дорожной карты."""
    roadmap = await roadmap_crud.get_user_roadmap(
        intern_id=user.id,
        session=session,
    )
    if not roadmap:
        await message.answer(' У пользователя нет назначенной дорожной карты.')
        return

    lines = []

    lines.append(f'📌 Дорожная карта: {roadmap.name}')
    for index, point in enumerate(roadmap.reference_points, start=1):
        point_type = point.point_type
        is_completed = point.is_completed
        check_datetime = point.check_datetime
        if is_completed:
            status_icon = '✅ Выполнено'
        elif check_datetime:
            status_icon = '⏳ В процессе'
            if check_datetime < datetime.now():
                status_icon += ', просрочено!⚠️'
        else:
            status_icon = '🔘 Не начато'
        lines.append(
            f'Шаг {index}: {point_type}\n  Статус: {status_icon}\n',
        )

    message_text = '\n'.join(lines).strip()

    if not message_text:
        await message.answer(
            '⚠️ Не удалось получить информацию о дорожной карте.',
        )
    else:
        await message.answer(message_text)
