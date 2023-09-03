from typing import Type

from aiogram import F, Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import scoped_session

from app.bot.keyboards import cmd_report_kb, main_menu
from app.bot.middlewares import DataBaseSessionMiddleWare
from app.db.managers import ModelManager
from app.db.models import User

from .states import BudgetState

router = Router()
router.message.middleware(DataBaseSessionMiddleWare())


@router.message(Command("test"))
async def cmd_test(
    message: types.Message, model_managers: dict[str, Type[ModelManager]]
):
    await message.answer(f'{model_managers["user"].list()}')


@router.message(Command("start"))
async def cmd_start(
    message: types.Message,
    model_managers: dict[str, Type[ModelManager]],
    user: User,
):
    mgr = model_managers["user"]
    if user is None:
        text = """Вас приветсвует Бюджетный Менеджер!
        Чтобы начать пользоваться менеджером, 
        создайте новый бюджет в нужной вам валюте и несколько категорий
        доходов и расходов для удобства."""
        mgr.create(tg_id=message.from_user.id)
    else:
        text = """С возвращением, уважаемый! Вы можете продолжить работу с вашим бюджетом"""
    await message.answer(text)


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cmd_cancel(message: types.Message, state: FSMContext, user: User):
    print(user)
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
