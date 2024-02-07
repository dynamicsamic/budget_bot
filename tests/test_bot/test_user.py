from datetime import datetime

import pytest
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Message, Update

from app.bot.callback_data import SignupUserCallbackData
from app.bot.replies import buttons, keyboards, prompts
from app.bot.states import CreateUser
from app.db.repository import UserRepository

from ..test_utils import TARGET_USER_ID
from .conftest import chat, user


@pytest.mark.asyncio
async def test_signup_new_user(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.choose_action)
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
    assert message.text == prompts.choose_budget_currency
    assert message.reply_markup == keyboards.create_callback_buttons(
        button_names={
            "изменить": "set_currency",
            "принять": "finish",
        },
        callback_prefix="signup_user",
    )
    state = await requester.get_fsm_state()
    assert state == CreateUser.choose_action


@pytest.mark.asyncio
async def test_signup_inactive_user(
    persistent_db_session,
    create_test_data,
    requester,
):
    await requester.set_fsm_state(CreateUser.choose_action)

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


@pytest.mark.asyncio
async def test_signup_active_user(
    create_test_data,
    requester,
):
    await requester.set_fsm_state(CreateUser.choose_action)

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
    assert message.text == prompts.signup_active_user
    assert message.reply_markup == keyboards.button_menu(buttons.main_menu)

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_signup_user_request_currency(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.choose_action)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=SignupUserCallbackData(action="set_currency").pack(),
        message=Message(
            message_id=1,
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
    assert message.text == prompts.budget_currency_description

    state = await requester.get_fsm_state()
    assert state == CreateUser.set_budget_currency


@pytest.mark.asyncio
async def test_signup_user_set_currency(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.set_budget_currency)

    valid_currency = "USD"
    msg = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=valid_currency,
    )
    await requester.make_request(SendMessage, Update(update_id=1, message=msg))

    message = requester.read_last_sent_message()
    assert message.text == prompts.signup_user_show_currency_and_finish(
        valid_currency
    )
    assert message.reply_markup == keyboards.create_callback_buttons(
        button_names={
            "завершить": "finish",
        },
        callback_prefix="signup_user",
    )

    state = await requester.get_fsm_state()
    assert state == CreateUser.choose_action

    data = await requester.get_fsm_state_data()
    assert data == {"budget_currency": valid_currency}
