from datetime import datetime

import pytest
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Message, Update

from app.bot.states import CreateUser
from app.bot.string_constants import (
    CANCEL_CALL,
    CANCEL_COMMAND,
    SHOW_MAIN_MENU_CALL,
    SHOW_MAIN_MENU_COMMAND,
    START_COMMAND,
)
from app.bot.templates.const import (
    cancel_operation,
    main_menu,
    start_message_active,
    start_message_anonymous,
    start_message_inactive,
)
from app.db.repository import UserRepository

from ..test_utils import TARGET_USER_ID, assert_uses_template
from .conftest import chat, user

start_message = Message(
    message_id=2,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text=f"/{START_COMMAND}",
)


@pytest.mark.asyncio
async def test_anonymous_user_start_command(create_test_tables, requester):
    await requester.make_request(
        SendMessage, Update(update_id=1, message=start_message)
    )

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, start_message_anonymous)

    state = await requester.get_fsm_state()
    assert state == CreateUser.choose_signup_type


@pytest.mark.asyncio
async def test_active_user_start_command(create_test_data, requester):
    await requester.make_request(
        SendMessage, Update(update_id=1, message=start_message)
    )

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, start_message_active)

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

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, start_message_inactive)

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_cancel_command(create_test_data, requester):
    cancel_message = Message(
        message_id=2,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=f"/{CANCEL_COMMAND}",
    )

    await requester.make_request(
        SendMessage, Update(update_id=1, message=cancel_message)
    )

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, cancel_operation)

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_cancel_callback(create_test_data, requester):
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=CANCEL_CALL,
        message=Message(
            message_id=2,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text=CANCEL_CALL,
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=callback),
    )

    answer = requester.read_last_sent_message()
    assert answer.text == cancel_operation["text"]
    assert answer.reply_markup == cancel_operation["reply_markup"]

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_show_main_menu_command(create_test_data, requester):
    main_menu_command = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=f"/{SHOW_MAIN_MENU_COMMAND}",
    )

    await requester.make_request(
        SendMessage, Update(update_id=1, message=main_menu_command)
    )

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, main_menu)


@pytest.mark.asyncio
async def test_show_main_menu_callback(create_test_data, requester):
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=SHOW_MAIN_MENU_CALL,
        message=Message(
            message_id=2,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text=SHOW_MAIN_MENU_CALL,
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=callback),
    )

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, main_menu)

    state = await requester.get_fsm_state()
    assert state is None
