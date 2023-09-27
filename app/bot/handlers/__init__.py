from aiogram import Router

from app.bot.middlewares import CurrentUserMiddleWare

from .budget import router as budget_router
from .callbacks import router as callback_router
from .category import router as category_router
from .commands import router as command_router
from .entry import router as entry_router

router = Router()
router.include_routers(
    budget_router,
    command_router,
    category_router,
    callback_router,
    entry_router,
)
router.message.middleware(CurrentUserMiddleWare())
router.callback_query.middleware(CurrentUserMiddleWare())
