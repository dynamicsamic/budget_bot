from datetime import datetime

import pytest
from aiogram.methods import AnswerCallbackQuery
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, Update

from app.bot import keyboards

from .conftest import chat, user

cancel_callback = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data=keyboards.buttons.cancel_operation.callback_data,
    message=Message(
        message_id=2,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=keyboards.buttons.cancel_operation.text,
    ),
)


@pytest.mark.asyncio
async def test_cancel_callback(create_test_data, requester):
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=cancel_callback),
    )

    message = requester.read_last_sent_message()
    expected_text = "Действие отменено"
    expected_markup = ReplyKeyboardRemove()
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state is None
