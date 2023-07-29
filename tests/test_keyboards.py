import pytest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards import cmd_report_kb


@pytest.mark.current
def test_cmd_report_kb():
    assert isinstance(cmd_report_kb, InlineKeyboardBuilder)
    buttons = list(cmd_report_kb.buttons)

    assert buttons[0].text == "Доходы"
    assert buttons[0].callback_data == "check_income"

    assert buttons[1].text == "Расходы"
    assert buttons[1].callback_data == "check_expenses"

    assert buttons[2].text == "Разница доход-расход"
    assert buttons[2].callback_data == "check_balance"
