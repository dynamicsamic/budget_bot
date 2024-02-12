from datetime import datetime

import pytest
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, Update

from app.bot.handlers.shared import (
    cancel_callback,
    cancel_command,
    show_main_menu_callback,
    show_main_menu_command,
    start_command,
)
from app.bot.replies import prompts
from app.bot.replies.keyboards.common import (
    show_main_menu,
    switch_to_main_or_cancel,
)
from app.bot.replies.keyboards.user import (
    user_activation_menu,
    user_signup_menu,
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
    assert message.text == prompts.start_message_anonymous
    assert message.reply_markup == user_signup_menu

    state = await requester.get_fsm_state()
    assert state == CreateUser.start


@pytest.mark.asyncio
async def test_active_user_start_command(create_test_data, requester):
    await requester.make_request(
        SendMessage, Update(update_id=1, message=start_message)
    )

    message = requester.read_last_sent_message()
    assert message.text == prompts.start_message_active
    assert message.reply_markup == switch_to_main_or_cancel

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
    assert message.text == prompts.start_message_inactive
    assert message.reply_markup == user_activation_menu

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
    assert message.text == prompts.cancel_operation_note
    assert message.reply_markup == ReplyKeyboardRemove()

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
    assert message.text == prompts.cancel_operation_note
    assert message.reply_markup == ReplyKeyboardRemove()

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
    assert message.text == prompts.main_menu_note
    assert message.reply_markup == show_main_menu


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
    assert message.text == prompts.main_menu_note
    assert message.reply_markup == show_main_menu

    state = await requester.get_fsm_state()
    assert state is None
