from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa
from sqlalchemy.orm import selectinload

from crud.users import user_crud
from models.models import (
    Dialog,
    ReferencePoint,
    RoadMap,
    Test,
    User,
    UserRoadMap,
)

user_set = {
    'user': {
        'id': 42,
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'tg_id': 123456789,
        'timezone': 'Europe/Moscow',
        'manager_id': 987765321,
        'bot_is_started': False,
        'is_active': True,
        'role': 'intern',
    },
    'roadmap': {
        'id': 1,
        'title': 'Адаптация нового сотрудника',
        'description': 'Программа ввода в должность',
    },
    'progress': {
        'id': 100,
        'started_at': '2025-05-01T10:00:00',
        'completed': False,
    },
    'checkpoints': [
        {
            'id': 1,
            'point_type': 'notification',
            'reminder_days_before': 0,
            'data': {
                'text': 'Добро пожаловать в компанию!',
            },
            'intern_start_checkpoint_date': '2025-05-01T10:00:00',
            'intern_finish_checkpoint_date': '2025-05-01T10:30:00',
            'manager_control_finish_checkpoint_date': '2025-05-02T12:00:00',
            'status': '✅',
        },
        {
            'id': 2,
            'point_type': 'test',
            'reminder_days_before': 1,
            'data': {
                'questions': ['Что такое FIFO?', 'Где найти график?'],
            },
            'intern_start_checkpoint_date': '2025-05-02T09:00:00',
            'intern_finish_checkpoint_date': None,
            'manager_control_finish_checkpoint_date': None,
            'status': '⏳',
        },
        {
            'id': 3,
            'point_type': 'feedback',
            'reminder_days_before': 0,
            'data': {
                'prompt': 'Поделитесь впечатлениями о первом дне.',
            },
            'intern_start_checkpoint_date': None,
            'intern_finish_checkpoint_date': None,
            'manager_control_finish_checkpoint_date': None,
            'status': 'not_started',
        },
    ],
}


def get_user_data(tg_id: int) -> dict:
    """Здесь будет извлечение данных из БД."""
    return {
        'user': user_set.get('user'),
        'roadmap': user_set.get('roadmap'),
        'progress': user_set.get('progress'),
        'checkpoints': user_set.get('checkpoints', []),
    }


# Здесь пока черновик
async def get_status_road_map(
    user_tg_id: int,
    session: AsyncSession,
) -> dict:
    """Получаем объект дорожной карты интерна."""
    stmt = (
        select(User)
        .where(User.tg_id == user_tg_id)
        .options(
            selectinload(User.roadmaps)
            .selectinload(UserRoadMap.roadmap)
            .selectinload(RoadMap.reference_points),
        )
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        return {'error': 'Пользователь не найден'}

    user_roadmap = next(
        (ur for ur in user.roadmaps if ur.roadmap and ur.roadmap.is_active),
        None,
    )

    if not user_roadmap or not user_roadmap.roadmap:
        return {'error': 'Нет дорожной карты'}

    roadmap = user_roadmap.roadmap
    referencepoints = roadmap.reference_points

    checkpoints = [
        {
            'id': rp.id,
            'order': rp.order_execution,
            'completed': rp.is_completed,
            'blocked': rp.is_blocked,
            'trigger': rp.trigger_datetime,
            'completed_at': rp.completion_datetime,
            'type': rp.point_type,
            'auto_closing': rp.auto_closing,
        }
        for rp in referencepoints
    ]

    return {
        'roadmap_id': roadmap.id,
        'roadmap_name': roadmap.name,
        'checkpoints': checkpoints,
    }


async def complete_ref_point(
    reference_point: ReferencePoint,
    scheduler: AsyncIOScheduler,
    session: AsyncSession,
) -> None:
    """Ставит галочку выполнено контрольной точке."""
    reference_point.is_completed = True
    reference_point.completion_datetime = datetime.now()
    scheduler.remove_job(str(reference_point.id))
    session.add(reference_point)
    await session.commit()


async def get_active_reference_points_for_user(
        user_id: int,
        session: AsyncSession,
    ) -> Optional[ReferencePoint]:
    """Получить активные точки стажера."""
    result = await session.execute(
        select(ReferencePoint)
        .options(
            selectinload(ReferencePoint.test).selectinload(Test.questions),
            selectinload(ReferencePoint.notification),
            selectinload(ReferencePoint.feedback_request),
        )
        .join(ReferencePoint.roadmap)
        .join(UserRoadMap, UserRoadMap.roadmap_id == ReferencePoint.roadmap_id)
        .where(
            UserRoadMap.user_id == user_id,
            ReferencePoint.is_completed.is_(False),
        )
        .order_by(ReferencePoint.order_execution),
    )
    return result.scalars().all()


async def get_active_reference_point_for_user(
        user_id: int,
        session: AsyncSession,
    ) -> Optional[ReferencePoint]:
    """Получить последнюю точку стажера."""
    result = await session.execute(
        select(ReferencePoint)
        .options(
            selectinload(ReferencePoint.test).selectinload(Test.questions),
            selectinload(ReferencePoint.notification),
            selectinload(ReferencePoint.feedback_request),
        )
        .join(ReferencePoint.roadmap)
        .join(UserRoadMap, UserRoadMap.roadmap_id == ReferencePoint.roadmap_id)
        .where(
            UserRoadMap.user_id == user_id,
            ReferencePoint.is_completed.is_(False),
        )
        .order_by(-ReferencePoint.order_execution)
        .limit(1),
    )
    return result.scalars().first()


async def save_message(
        sender_id: int,
        recipient_id: int,
        text: str,
        session: AsyncSession,
) -> None:
    """Сохранить сообщение в БД."""
    sender = await user_crud.get_user_by_tg_id(session, sender_id)
    receiver = await user_crud.get_user_by_tg_id(session, recipient_id)
    dialog = Dialog(
        sender_id=sender.id,
        recipient_id=receiver.id,
        message=text,
        message_datetime=datetime.now(),
    )
    session.add(dialog)
    await session.commit()
