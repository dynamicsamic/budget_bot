from datetime import datetime

import pytest
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Message, Update

from app.bot.replies.templates.common import (
    cancel_operation,
    main_menu,
    start_message_active,
    start_message_anonymous,
    start_message_inactive,
)
from app.bot.shared import (
    cancel_callback,
    cancel_command,
    show_main_menu_callback,
    show_main_menu_command,
    start_command,
)
from app.bot.states import CreateUser
from app.db.repository import UserRepository

from ..test_utils import TARGET_USER_ID
from .conftest import chat, user

start_message = Message(
    message_id=2,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text=f"/{start_command}",
)


@pytest.mark.asyncio
async def test_anonymous_user_start_command(create_test_tables, requester):

    await requester.make_request(
        SendMessage, Update(update_id=1, message=start_message)
    )

    message = requester.read_last_sent_message()
    assert message.text == start_message_anonymous["text"]
    assert message.reply_markup == start_message_anonymous["reply_markup"]

    state = await requester.get_fsm_state()
    assert state == CreateUser.choose_signup_type


@pytest.mark.asyncio
async def test_active_user_start_command(create_test_data, requester):
    await requester.make_request(
        SendMessage, Update(update_id=1, message=start_message)
    )

    message = requester.read_last_sent_message()
    assert message.text == start_message_active["text"]
    assert message.reply_markup == start_message_active["reply_markup"]

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_inactive_user_start_command(
    persistent_db_session, create_test_data, requester
):
    repo = UserRepository(persistent_db_session)
    repo.update_user(TARGET_USER_ID, is_active=False)

    await requester.make_request(
        SendMessage, Update(update_id=1, message=start_message)
    )

    message = requester.read_last_sent_message()
    assert message.text == start_message_inactive["text"]
    assert message.reply_markup == start_message_inactive["reply_markup"]

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_cancel_command(create_test_data, requester):
    cancel_message = Message(
        message_id=2,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=f"/{cancel_command}",
    )

    await requester.make_request(
        SendMessage, Update(update_id=1, message=cancel_message)
    )

    message = requester.read_last_sent_message()
    assert message.text == cancel_operation["text"]
    assert message.reply_markup == cancel_operation["reply_markup"]

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_cancel_callback(create_test_data, requester):
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=cancel_callback,
        message=Message(
            message_id=2,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text=cancel_callback,
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=callback),
    )

    message = requester.read_last_sent_message()
    assert message.text == cancel_operation["text"]
    assert message.reply_markup == cancel_operation["reply_markup"]

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_show_main_menu_command(create_test_data, requester):
    main_menu_command = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=f"/{show_main_menu_command}",
    )

    await requester.make_request(
        SendMessage, Update(update_id=1, message=main_menu_command)
    )

    message = requester.read_last_sent_message()
    assert message.text == main_menu["text"]
    assert message.reply_markup == main_menu["reply_markup"]


@pytest.mark.asyncio
async def test_show_main_menu_callback(create_test_data, requester):
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=show_main_menu_callback,
        message=Message(
            message_id=2,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text=show_main_menu_callback,
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=callback),
    )

    message = requester.read_last_sent_message()
    assert message.text == main_menu["text"]
    assert message.reply_markup == main_menu["reply_markup"]

    state = await requester.get_fsm_state()
    assert state is None
