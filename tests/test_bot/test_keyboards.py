from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot import string_constants as sc
from app.bot.templates.buttons import cancel_operation, switch_to_main_menu
from app.bot.templates.keyboards import (
    category_type_menu,
    category_update_options,
    cmd_report_kb,
)


def test_cmd_report_kb():
    assert isinstance(cmd_report_kb, InlineKeyboardBuilder)
    buttons = list(cmd_report_kb.buttons)

    assert buttons[0].text == "Доходы"
    assert buttons[0].callback_data == "check_income"

    assert buttons[1].text == "Расходы"
    assert buttons[1].callback_data == "check_expenses"

    assert buttons[2].text == "Разница доход-расход"
    assert buttons[2].callback_data == "check_balance"


def test_category_type_menu():
    main_buttons, extra_buttons = category_type_menu.inline_keyboard

    income_btn, expenses_btn = main_buttons
    assert income_btn.text == "Доходы"
    assert income_btn.callback_data == f"{sc.SELECT_CATEGORY_TYPE}:income"
    assert expenses_btn.text == "Расходы"
    assert expenses_btn.callback_data == f"{sc.SELECT_CATEGORY_TYPE}:expenses"

    cancel_btn, main_menu_btn = extra_buttons
    assert cancel_btn == cancel_operation
    assert main_menu_btn == switch_to_main_menu


def test_category_update_options():
    btn1, btn2, btn3 = category_update_options.inline_keyboard[0]

    assert btn1.text == "название".capitalize()
    assert btn1.callback_data == f"{sc.UPDATE_CATEGORY}:name"

    assert btn2.text == "тип".capitalize()
    assert btn2.callback_data == f"{sc.UPDATE_CATEGORY}:type"

    assert btn3.text == "завершить".capitalize()
    assert btn3.callback_data == f"{sc.UPDATE_CATEGORY}:finish"
