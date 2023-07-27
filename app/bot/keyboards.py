from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

cmd_report_kb = InlineKeyboardBuilder()
cmd_report_kb.row(
    types.InlineKeyboardButton(text="Доходы", callback_data="check_income"),
    types.InlineKeyboardButton(text="Расходы", callback_data="check_expenses"),
    types.InlineKeyboardButton(
        text="Разница доход-расход", callback_data="check_balance"
    ),
)
