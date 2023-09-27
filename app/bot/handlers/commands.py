from typing import Type

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import scoped_session

from app.bot.keyboards import cmd_report_kb, main_menu
from app.bot.middlewares import ModelManagerMiddleware
from app.db.managers import DateQueryManager, EntryManager, ModelManagerStore
from app.db.models import User

router = Router()
router.message.middleware(ModelManagerMiddleware())


@router.message(
    Command("test"),
    flags=ModelManagerStore.as_flags("user", "budget", "category", "entry"),
)
async def cmd_test(
    message: types.Message,
    user_manager: DateQueryManager,
    budget_manager: DateQueryManager,
    category_manager: DateQueryManager,
    entry_manager: EntryManager,
):
    users = user_manager.list()
    budgets = budget_manager.list()
    categories = category_manager.list()
    entries = entry_manager.list()
    await message.answer(f"{users}, {budgets}, {categories}, {entries}")


@router.message(Command("start"), flags=ModelManagerStore.as_flags("user"))
async def cmd_start(
    message: types.Message, user: User, user_manager: DateQueryManager
):
    if user is None:
        text = """Вас приветсвует Бюджетный Менеджер!
        Чтобы начать пользоваться менеджером, 
        создайте новый бюджет в нужной вам валюте и несколько категорий
        доходов и расходов для удобства."""
        user_manager.create(tg_id=message.from_user.id)
    else:
        text = """С возвращением, уважаемый! Вы можете продолжить работу с вашим бюджетом"""
    await message.answer(text)


@router.message(Command("cancel"), F.text.casefold() == "отмена")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Действие отменено", reply_markup=types.ReplyKeyboardRemove()
    )


@router.message(Command("show_menu"))
async def cmd_show_menu(message: types.Message):
    await message.answer("Основное меню", reply_markup=main_menu.as_markup())


@router.message(Command("get_report"))
async def cmd_get_report(message: types.Message):
    await message.answer(
        "Выберите тип отчета", reply_markup=cmd_report_kb.as_markup()
    )
