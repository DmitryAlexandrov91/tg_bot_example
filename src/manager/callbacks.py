
from aiogram.filters.callback_data import CallbackData


class ManagerStartCallback(CallbackData, prefix='start'):
    """Класс обработки стартовых команд."""

    action: str


class ManagerTemplateRoadmapCallback(CallbackData, prefix='tmproadmap'):
    """Класс обработки кнопок меню Шаблона дорожной карты."""

    templateroadmap_id: int
    action: str


class ManagerRoadmapCallback(CallbackData, prefix='roadmap'):
    """Класс обработки кнопок меню Дорожной карты."""

    roadmap_id: int
    intern_id: int
    action: str


class ManagerTemplateReferencepointCallback(
    CallbackData, prefix='tmpreferencepoint',
):
    """Класс обработки кнопок выбора Шаблона чекпоинта."""

    templatereferencepoint_id: int
    action: str


class ManagerReferencepointCallback(CallbackData, prefix='referencepoint'):
    """Класс обработки кнопок выбора Чекпоинта."""

    referencepoint_id: int
    intern_id: int
    action: str


class ManagerInternCallback(CallbackData, prefix='intern'):
    """Класс обработки кнопок выбора Стажёра."""

    action: str
    intern_id: int


class ManagerAssignRoadmapCallback(CallbackData, prefix='add_roadmap'):
    """Класс обработки назначения дорожной карты."""

    templateroadmap_id: int
    intern_id: int
    action: str


class ManagerUploadRoadmapCallback(CallbackData, prefix='upload_roadmap'):
    """Класс обработки загрузки дорожной карты."""

    action: str
