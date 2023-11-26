from typing import Callable

import pytest
from aiogram.filters.command import Command
from aiogram_tests import MockedBot
from aiogram_tests.handler import CallbackQueryHandler, MessageHandler
from aiogram_tests.types.dataset import CALLBACK_QUERY, MESSAGE

from app.bot.handlers.commands import cmd_get_report, cmd_start


def uses_keyboard(fn: Callable, kb_name: str) -> bool:
    return kb_name in fn.__code__.co_names


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
        MessageHandler(cmd_get_report, Command(commands=["get_report"]))
    )
    calls = await requester.query(MESSAGE.as_object(text="/get_report"))
    answer_message = calls.send_message.fetchone().text

    assert answer_message == "Выберите тип отчета"
    assert "inline_keyboard" in calls.send_message.fetchone().reply_markup
    assert uses_keyboard(cmd_get_report, "cmd_report_kb")
