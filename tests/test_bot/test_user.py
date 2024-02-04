from datetime import datetime

import pytest
from aiogram.enums import ChatType
from aiogram.methods import AnswerCallbackQuery
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from app.bot.handlers import shared
from app.bot.replies import keyboards, prompts

anonymous_user = User(
    id=999, is_bot=False, first_name="anonymous", username="anonymous"
)
anonymous_chat = Chat(id=999, type=ChatType.PRIVATE)


@pytest.mark.asyncio
async def test_signup_anonymous(create_test_data, requester):
    callback = CallbackQuery(
        id="12345678",
        from_user=anonymous_user,
        chat_instance="AABBCC",
        data=shared.signup_user,
        message=Message(
            message_id=2,
            date=datetime.now(),
            from_user=anonymous_user,
            chat=anonymous_chat,
            text="text",
        ),
    )
    await requester.make_request(
        AnswerCallbackQuery, Update(update_id=1, callback_query=callback)
    )

    message = requester.read_last_sent_message()
    assert message.text == prompts.choose_budget_currency
    assert message.reply_markup == keyboards.create_callback_buttons(
        button_names={
            "изменить": "set_currency",
            "принять": "finish",
        },
        callback_prefix="create_user",
    )
