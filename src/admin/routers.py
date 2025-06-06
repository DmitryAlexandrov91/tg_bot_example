from aiogram import Router

from admin.handlers import (
    invitations_router,
    restaurants_router,
    roadmap_templates_router,
    template_ref_point_router,
    users_router,
)
from middlewares import cancel_middleware

admin_router = Router()
admin_router.message.middleware(cancel_middleware)
admin_router.include_router(users_router)
admin_router.include_router(restaurants_router)
admin_router.include_router(invitations_router)
admin_router.include_router(roadmap_templates_router)
admin_router.include_router(template_ref_point_router)
