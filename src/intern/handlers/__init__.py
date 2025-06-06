from aiogram import Router

from .dialogue import dialogue_router
from .notifications import notifications_router  # noqa
from .status_checkpoint import status_point_router  # noqa
from .status_roadmap import status_roadmap_router  # noqa
from .termination_roadmap import term_roadmap_router  # noqa

intern_router = Router()

intern_router.include_routers(
    status_roadmap_router,
    term_roadmap_router,
    dialogue_router,
    notifications_router,
    status_point_router,
)
