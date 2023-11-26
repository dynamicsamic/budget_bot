import pytest
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram_tests import MockedBot
from aiogram_tests.handler import CallbackQueryHandler, MessageHandler
from aiogram_tests.types.dataset import CALLBACK_QUERY, MESSAGE

from app.bot.handlers.callbacks import cb_check_income


@pytest.mark.asyncio
async def test_cb_check_income():
    requester = MockedBot(CallbackQueryHandler(cb_check_income))
    callback_query = CALLBACK_QUERY.as_object(
        data="check_income", message=MESSAGE.as_object(text="Hello world!")
    )
    calls = await requester.query(callback_query)

    answer_text = calls.send_message.fetchone().text
    assert answer_text == "Выберите период"
