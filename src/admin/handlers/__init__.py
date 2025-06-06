from aiogram import Dispatcher  # noqa

from .invitations import router as invitations_router  # noqa
from .restaurants import router as restaurants_router  # noqa

from .roadmaps import router as roadmap_templates_router  # noqa
from .reference_points import router as template_ref_point_router  # noqa
# from .tests import router as tests_rouet  # noqa
from .users import router as users_router  # noqa
