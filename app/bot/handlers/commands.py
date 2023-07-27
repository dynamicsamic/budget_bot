from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards import cmd_report_kb


async def cmd_start(message: types.Message):
    await message.answer("Привет, юзер!")


async def cmd_get_report(message: types.Message):
    await message.answer(
        "Выберите тип отчета", reply_markup=cmd_report_kb.as_markup()
    )
