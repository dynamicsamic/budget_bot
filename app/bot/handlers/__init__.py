from aiogram import Router

from app.bot.middlewares import (
    DbSessionMiddleWare,
    IdentifyUserMiddleWare,
    RedirectAnonymousUserMiddleWare,
)

from .budget import router as budget_router
from .callbacks import router as callback_router
from .category import router as category_router
from .commands import router as command_router
from .entry import router as entry_router
from .user import router as user_router

router = Router()
router.include_routers(
    budget_router,
    command_router,
    category_router,
    callback_router,
    entry_router,
    user_router,
)
router.message.middleware(DbSessionMiddleWare())
router.message.middleware(IdentifyUserMiddleWare())
router.message.middleware(RedirectAnonymousUserMiddleWare())
router.callback_query.middleware(DbSessionMiddleWare())
router.callback_query.middleware(IdentifyUserMiddleWare())
router.callback_query.middleware(RedirectAnonymousUserMiddleWare())
