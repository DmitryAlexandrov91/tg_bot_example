from aiogram import Router

from .interns import router as interns_router
from .manager_menu import router as start_help_router
from .referencepoints import router as referencepoint_router
from .roadmaps import router as roadmaps_router
from .template_referencepoints import (
    router as template_referencepoints_router,
)
from .template_roadmaps import router as template_roadmaps_router

manager_router = Router()

manager_router.include_routers(
    interns_router,
    referencepoint_router,
    roadmaps_router,
    start_help_router,
    template_referencepoints_router,
    template_roadmaps_router,
)
