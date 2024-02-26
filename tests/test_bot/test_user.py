from datetime import datetime

import pytest
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Message, Update

from app.bot.callback_data import SignupUserCallbackData
from app.bot.replies.keyboards import buttons
from app.bot.replies.templates import error as ert
from app.bot.replies.templates import user as ust
from app.bot.states import CreateUser
from app.db.repository import UserRepository

from .conftest import chat, user


@pytest.mark.asyncio
async def test_signup_new_user(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.choose_signup_type)
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

    text, reply_markup = ust.choose_signup_type.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == reply_markup

    state = await requester.get_fsm_state()
    assert state == CreateUser.choose_signup_type

    data = await requester.get_fsm_state_data()
    assert data.get("tg_id") == user.id


@pytest.mark.asyncio
async def test_start_advanced_signup(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.choose_signup_type)
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=SignupUserCallbackData(action="advanced").pack(),
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

    text, reply_markup = ust.advanced_signup_menu.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == reply_markup

    state = await requester.get_fsm_state()
    assert state == CreateUser.advanced_signup


@pytest.mark.asyncio
async def test_request_currency(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.advanced_signup)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=SignupUserCallbackData(action="get_currency").pack(),
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
    assert message.text == ust.budget_currency_description["text"]
    assert (
        message.reply_markup == ust.budget_currency_description["reply_markup"]
    )
    assert message.reply_markup is None

    state = await requester.get_fsm_state()
    assert state == CreateUser.get_budget_currency


@pytest.mark.asyncio
async def test_set_valid_currency(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.get_budget_currency)

    valid_currency = "USD"
    msg = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=valid_currency,
    )
    await requester.make_request(SendMessage, Update(update_id=1, message=msg))

    text, markup = ust.show_currency(valid_currency).values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state == CreateUser.choose_signup_type

    data = await requester.get_fsm_state_data()
    assert data.get("budget_currency") == valid_currency


@pytest.mark.asyncio
async def test_set_invalid_currency(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.get_budget_currency)

    valid_currency = "$USD/"
    msg = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=valid_currency,
    )
    await requester.make_request(SendMessage, Update(update_id=1, message=msg))

    text, markup = ert.invalid_budget_currency.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state == CreateUser.get_budget_currency

    data = await requester.get_fsm_state_data()
    assert "budget_currency" not in data


@pytest.mark.asyncio
async def test_finish_signup(
    create_test_tables, requester, persistent_db_session
):
    repository = UserRepository(persistent_db_session)
    initial_user_count = repository.count_users()
    assert initial_user_count == 0

    currency = "USD"
    await requester.set_fsm_state(CreateUser.choose_signup_type)
    await requester.update_fsm_state_data(
        tg_id=user.id, budget_currency=currency
    )

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=SignupUserCallbackData(action="basic").pack(),
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

    current_user_count = repository.count_users()
    assert current_user_count == initial_user_count + 1

    created_user = repository.get_user(tg_id=user.id)
    text, markup = ust.show_signup_summary(created_user).values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_finish_signup_basic(
    create_test_tables, requester, persistent_db_session
):
    repository = UserRepository(persistent_db_session)
    initial_user_count = repository.count_users()
    assert initial_user_count == 0

    await requester.set_fsm_state(CreateUser.choose_signup_type)
    await requester.update_fsm_state_data(tg_id=user.id)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=SignupUserCallbackData(action="basic").pack(),
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

    current_user_count = repository.count_users()
    assert current_user_count == initial_user_count + 1

    created_user = repository.get_user(tg_id=user.id)
    text, markup = ust.show_signup_summary(created_user).values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup
    assert created_user.budget_currency == "RUB"

    state = await requester.get_fsm_state()
    assert state is None
