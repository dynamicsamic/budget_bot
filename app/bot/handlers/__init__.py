from aiogram import Router

from .budget import router as budget_router
from .commands import router as command_router

router = Router()
router.include_routers(budget_router, command_router)
