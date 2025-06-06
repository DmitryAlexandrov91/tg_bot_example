import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Type, TypeVar

from config import BASE_DIR
from engine import session_maker
from models.models import (
    Dialog,
    FeedbackRequest,
    InvitationLink,
    Notification,
    Question,
    ReferencePoint,
    Restaurant,
    RoadMap,
    TemplateFeedbackRequest,
    TemplateNotification,
    TemplateQuestion,
    TemplateReferencePoint,
    TemplateRoadMap,
    TemplateTest,
    Test,
    User,
    UserRoadMap,
)

DATA_DIR = BASE_DIR / 'data'
Model = TypeVar('Model')


class DataLoader:
    """Класс для загрузки данных в базу данных с соблюдением принципов DRY."""

    @staticmethod
    def load_json(filepath: str) -> List[Dict[str, Any]]:
        """Загружает данные из JSON файла."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def parse_datetime_fields(
        data: Dict[str, Any],
        datetime_fields: List[str],
    ) -> Dict[str, Any]:
        """Парсит указанные поля в datetime объекты."""
        for field in datetime_fields:
            if field in data and data[field]:
                data[field] = datetime.strptime(data[field], "%Y-%m-%d")
        return data

    @classmethod
    async def _bulk_insert(
        cls,
        session: Any,
        model: Type[Model],
        data: List[Dict[str, Any]],
        datetime_fields: List[str] = None,
    ) -> None:
        """Вспомогательный метод для массовой вставки данных."""
        if datetime_fields:
            data = [
                cls.parse_datetime_fields(
                    item, datetime_fields) for item in data
                ]

        session.add_all([model(**item) for item in data])
        await session.flush()

    @classmethod
    async def load_all_data(cls) -> None:
        """Загружает все данные из JSON файлов в базу данных."""
        file_mappings = {
            'restaurants': Restaurant,
            'users': User,

            'templateroadmap': TemplateRoadMap,
            'templatetests': TemplateTest,
            'templatereferencepoints': TemplateReferencePoint,
            'templatequestions': TemplateQuestion,
            'templatenotifications': TemplateNotification,
            'templatefeedbackrequests': TemplateFeedbackRequest,

            'roadmaps': RoadMap,
            'userroadmaps': UserRoadMap,
            'referencepoints': (
                ReferencePoint,
                ['trigger_datetime', 'check_datetime', 'completion_datetime'],
            ),
            'tests': Test,
            'feedbackrequests': FeedbackRequest,
            'notifications': Notification,
            'questions': Question,

            'invitationlinks': (InvitationLink, ['expires_at', 'created_at']),
            'dialogs': (Dialog, ['message_datetime']),
        }

        async with session_maker() as session:
            async with session.begin():
                for filename, model_info in file_mappings.items():
                    if isinstance(model_info, tuple):
                        model, datetime_fields = model_info
                    else:
                        model, datetime_fields = model_info, None
                    data = cls.load_json(f'{DATA_DIR}/{filename}.json')
                    await cls._bulk_insert(
                        session, model, data, datetime_fields)


async def main() -> None:
    """Точка входа для загрузки данных."""
    await DataLoader.load_all_data()


if __name__ == '__main__':
    asyncio.run(main())
