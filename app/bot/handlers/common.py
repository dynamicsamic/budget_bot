import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.bot.middlewares import UserRepositoryMiddleWare
from app.bot.replies.keyboards.common import (
    show_main_menu,
    switch_to_main_or_cancel,
)
from app.bot.replies.keyboards.entry import cmd_report_kb
from app.bot.replies.keyboards.user import (
    user_activation_menu,
    user_signup_menu,
)
from app.bot.states import CreateUser
from app.db.models import User
from app.utils import aiogram_log_handler

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)

router = Router()
router.message.middleware(UserRepositoryMiddleWare())


@router.message(Command("test"))
async def cmd_test(message: types.Message, state: FSMContext):
    pass


@router.message(Command("start"), flags={"allow_anonymous": True})
async def cmd_start(
    message: types.Message,
    state: FSMContext,
    user: User,
):
    if user.is_anonymous:
        await state.set_state(CreateUser.choose_action)
        await message.answer(
            """Вас приветсвует Бюджетный Менеджер!
            Чтобы начать пользоваться менеджером, 
            создайте новый бюджет в нужной вам валюте и несколько категорий
            доходов и расходов для удобства.""",
            reply_markup=user_signup_menu,
        )
    elif not user.is_active:
        await message.answer(
            """Вас приветсвует Бюджетный Менеджер!
            Чтобы возобновить работу с менеджером, 
            нажмите на кнопку `Активировать`.
            """,
            reply_markup=user_activation_menu,
        )
    else:
        await message.answer(
            """С возвращением в Бюджетный Менеджер!
            Продолжите работу в главном меню.
            """,
            reply_markup=switch_to_main_or_cancel,
        )


@router.message(Command("cancel"), F.text.casefold() == "отмена")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Действие отменено", reply_markup=types.ReplyKeyboardRemove()
    )
    logger.info("SUCCESS, operation canceled, state cleared")


@router.callback_query(F.data.casefold() == "cancel")
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        text="Действие отменено", reply_markup=types.ReplyKeyboardRemove()
    )
    await callback.answer()
    logger.info("SUCCESS, operation canceled, state cleared")


@router.message(Command("show_main_menu"))
async def cmd_show_menu(message: types.Message):
    await message.answer("Основное меню", reply_markup=show_main_menu)


@router.message(Command("get_report"))
async def cmd_get_report(message: types.Message):
    await message.answer(
        "Выберите тип отчета", reply_markup=cmd_report_kb.as_markup()
    )


@router.callback_query(F.data == "main_menu_return")
async def return_to_main_menu(
    callback: types.CallbackQuery, state: FSMContext
):
    await state.clear()
    await cmd_show_menu(callback.message)
    await callback.answer()
