import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.bot.middlewares import UserRepositoryMiddleWare
from app.bot.replies.keyboards.entry import cmd_report_kb
from app.bot.replies.templates.common import (
    cancel_operation,
    main_menu,
    start_message_active,
    start_message_anonymous,
    start_message_inactive,
)
from app.bot.states import CreateUser
from app.db.models import User
from app.utils import aiogram_log_handler

from . import shared

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)

router = Router()
router.message.middleware(UserRepositoryMiddleWare)


@router.message(Command(shared.start_command), flags={"allow_anonymous": True})
async def cmd_start(
    message: types.Message,
    state: FSMContext,
    user: User,
):
    if user.is_anonymous:
        await state.set_state(CreateUser.start)
        await message.answer(**start_message_anonymous)
    elif not user.is_active:
        await message.answer(**start_message_inactive)
    else:
        await message.answer(**start_message_active)


@router.message(Command(shared.cancel_command))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(**cancel_operation)
    logger.info("SUCCESS, operation canceled, state cleared")


@router.callback_query(F.data.casefold() == shared.cancel_callback)
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(**cancel_operation)
    await callback.answer()
    logger.info("SUCCESS, operation canceled, state cleared")


@router.message(Command(shared.show_main_menu_command))
async def cmd_show_menu(message: types.Message):
    await message.answer(**main_menu)
    logger.info("SUCCESS")


@router.message(Command("get_report"))
async def cmd_get_report(message: types.Message):
    await message.answer(
        "Выберите тип отчета", reply_markup=cmd_report_kb.as_markup()
    )


@router.callback_query(F.data == shared.show_main_menu_callback)
async def return_to_main_menu(
    callback: types.CallbackQuery, state: FSMContext
):
    await state.clear()
    await cmd_show_menu(callback.message)
    await callback.answer()


@router.message(Command("test"))
async def cmd_test(message: types.Message, state: FSMContext):
    pass
