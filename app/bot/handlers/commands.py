from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from app.bot.keyboards import cmd_report_kb

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет, юзер!")


@router.message(Command("cancel", ignore_case=True))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Действие отменено", reply_markup=types.ReplyKeyboardRemove()
    )


@router.message(Command("get_report"))
async def cmd_get_report(message: types.Message):
    await message.answer(
        "Выберите тип отчета", reply_markup=cmd_report_kb.as_markup()
    )
