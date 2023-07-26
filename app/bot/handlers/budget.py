from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def cmd_get_report(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Доходы", callback_data="check_income")
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Расходы", callback_data="check_expenses"
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Разница доход-расход", callback_data="check_balance"
        )
    )
    await message.answer(
        "Выберите тип отчета", reply_markup=builder.as_markup()
    )
