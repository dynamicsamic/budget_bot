from datetime import datetime

import pytest
from aiogram.enums import ChatType
from aiogram.methods import AnswerCallbackQuery
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from app.bot.replies import buttons, keyboards, prompts
from app.bot.states import UserCreateState
from app.db.repository import UserRepository

from ..test_utils import TARGET_USER_ID
from .conftest import chat, user

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
        data=buttons.signup_user.callback_data,
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
        callback_prefix="signup_user",
    )

    state = await requester.get_fsm_state()
    assert state == UserCreateState.wait_for_action


@pytest.mark.asyncio
async def test_signup_inactive_user(
    persistent_db_session, create_test_data, requester
):
    repository = UserRepository(persistent_db_session)
    repository.update_user(TARGET_USER_ID, is_active=False)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=buttons.signup_user.callback_data,
        message=Message(
            message_id=2,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="text",
        ),
    )
    await requester.make_request(
        AnswerCallbackQuery, Update(update_id=1, callback_query=callback)
    )

    message = requester.read_last_sent_message()
    assert message.text == prompts.signup_inactive_user
    assert message.reply_markup == keyboards.button_menu(
        buttons.activate_user,
        buttons.cancel_operation,
    )

    state = await requester.get_fsm_state()
    assert state is None
