import pytest
from aiogram.filters.command import Command
from aiogram_tests import MockedBot
from aiogram_tests.handler import CallbackQueryHandler, MessageHandler
from aiogram_tests.types.dataset import CALLBACK_QUERY, MESSAGE

from app.bot.handlers.commands import cmd_get_report, cmd_start


@pytest.mark.asyncio
async def test_cmd_start():
    requester = MockedBot(
        MessageHandler(cmd_start, Command(commands=["start"]))
    )
    calls = await requester.query(MESSAGE.as_object(text="/start"))
    answer_message = calls.send_message.fetchone().text
    assert answer_message == "Привет, юзер!"


@pytest.mark.asyncio
async def test_get_report():
    requester = MockedBot(
        MessageHandler(cmd_get_report, Command(commands=["report"]))
    )
    calls = await requester.query(MESSAGE.as_object(text="/report"))
    answer_message = calls.send_message.fetchone().text
    assert answer_message == "Выберите тип отчета"

    markup = calls.send_message.fetchone().reply_markup
    assert len(markup) == 1
    assert "inline_keyboard" in markup

    buttons = [button for lst in markup["inline_keyboard"] for button in lst]

    assert buttons[0]["text"] == "Доходы"
    assert buttons[0]["callback_data"] == "check_income"

    assert buttons[1]["text"] == "Расходы"
    assert buttons[1]["callback_data"] == "check_expenses"

    assert buttons[2]["text"] == "Разница доход-расход"
    assert buttons[2]["callback_data"] == "check_balance"
