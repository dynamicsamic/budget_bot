import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.bot import string_constants as sc
from app.bot.middlewares import UserRepositoryMiddleWare
from app.bot.states import CreateUser
from app.bot.templates.const import (
    cancel_operation,
    main_menu,
    start_message_active,
    start_message_anonymous,
    start_message_inactive,
)
from app.db.models import User
from app.utils import aiogram_log_handler

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)

router = Router()
router.message.middleware(UserRepositoryMiddleWare)


@router.message(Command(sc.START_COMMAND), flags={"allow_anonymous": True})
async def cmd_start(
    message: types.Message,
    state: FSMContext,
    user: User,
):
    if user.is_anonymous:
        await state.set_state(CreateUser.choose_signup_type)
        await message.answer(**start_message_anonymous)
    elif not user.is_active:
        await message.answer(**start_message_inactive)
    else:
        await message.answer(**start_message_active)


@router.message(Command(sc.CANCEL_COMMAND))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(**cancel_operation)
    logger.info("SUCCESS, operation canceled, state cleared")


@router.callback_query(F.data.casefold() == sc.CANCEL_CALL)
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(**cancel_operation)
    await callback.answer()
    logger.info("SUCCESS, operation canceled, state cleared")


@router.message(Command(sc.SHOW_MAIN_MENU_COMMAND))
async def cmd_show_menu(message: types.Message):
    await message.answer(**main_menu)
    logger.info("SUCCESS")


@router.callback_query(F.data == sc.SHOW_MAIN_MENU_CALL)
async def return_to_main_menu(
    callback: types.CallbackQuery, state: FSMContext
):
    await state.clear()
    await cmd_show_menu(callback.message)
    await callback.answer()


@router.message(Command("test"))
async def cmd_test(message: types.Message, state: FSMContext):
    pass
