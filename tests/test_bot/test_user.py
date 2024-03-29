from datetime import datetime

import pytest
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Message, Update

from app.bot import string_constants as sc
from app.bot.filters import (
    CurrencyUpdateData,
    UserSignupData,
)
from app.bot.states import CreateUser, UpdateUser
from app.bot.templates import const, func
from app.db.repository import UserRepository

from ..test_utils import TARGET_USER_ID, assert_uses_template
from .conftest import chat, user


@pytest.fixture
def repository(persistent_db_session):
    return UserRepository(persistent_db_session)


@pytest.mark.asyncio
async def test_signup_new_user(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.choose_signup_type)
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.SIGNUP_USER}:start",
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

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.choose_signup_type)

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
        data=UserSignupData(action="advanced").pack(),
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

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.advanced_signup_menu)

    state = await requester.get_fsm_state()
    assert state == CreateUser.advanced_signup


@pytest.mark.asyncio
async def test_request_currency(create_test_tables, requester):
    await requester.set_fsm_state(CreateUser.advanced_signup)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=UserSignupData(action="get_currency").pack(),
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

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.budget_currency_description)

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

    answer = requester.read_last_sent_message()
    assert_uses_template(
        answer, func.show_signup_currency, budget_currency=valid_currency
    )

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

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.invalid_budget_currency)

    state = await requester.get_fsm_state()
    assert state == CreateUser.get_budget_currency

    data = await requester.get_fsm_state_data()
    assert "budget_currency" not in data


@pytest.mark.asyncio
async def test_finish_signup(create_test_tables, requester, repository):
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
        data=UserSignupData(action="basic").pack(),
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
    answer = requester.read_last_sent_message()
    assert_uses_template(answer, func.show_signup_summary, user=created_user)

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_finish_signup_basic(create_test_tables, requester, repository):
    initial_user_count = repository.count_users()
    assert initial_user_count == 0

    await requester.set_fsm_state(CreateUser.choose_signup_type)
    await requester.update_fsm_state_data(tg_id=user.id)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=UserSignupData(action="basic").pack(),
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
    answer = requester.read_last_sent_message()
    assert_uses_template(answer, func.show_signup_summary, user=created_user)
    assert created_user.budget_currency == "RUB"

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_show_user_profile(create_test_data, requester):
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=sc.SHOW_USER_PROFILE,
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
    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.user_profile)


@pytest.mark.asyncio
async def test_show_anonymous_user_profile(create_test_tables, requester):
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=sc.SHOW_USER_PROFILE,
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
    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.redirect_anonymous)


@pytest.mark.asyncio
async def test_delete_user(create_test_data, persistent_db_session, requester):
    repo = UserRepository(persistent_db_session)
    db_user = repo.get_user(user_id=TARGET_USER_ID)
    assert db_user.is_active is True

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=sc.DELETE_USER,
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
    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.user_delete_summary)

    persistent_db_session.refresh(db_user)
    assert db_user.is_active is False


@pytest.mark.asyncio
async def test_update_budget_currency(create_test_data, requester):
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=CurrencyUpdateData(action="start").pack(),
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
    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.budget_currency_description)

    state = await requester.get_fsm_state()
    assert state == UpdateUser.budget_currency


@pytest.mark.asyncio
async def test_set_updated_currency(create_test_data, requester):
    await requester.set_fsm_state(UpdateUser.budget_currency)

    valid_currency = "Valid"
    msg = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=valid_currency,
    )

    await requester.make_request(SendMessage, Update(update_id=1, message=msg))

    answer = requester.read_last_sent_message()
    assert_uses_template(
        answer, func.confirm_updated_currency, budget_currency=valid_currency
    )

    data = await requester.get_fsm_state_data()
    assert data.get("budget_currency") == valid_currency


@pytest.mark.asyncio
async def test_set_invalid_updated_currency(create_test_data, requester):
    await requester.set_fsm_state(UpdateUser.budget_currency)

    invalid_currency = "inValid$"
    msg = Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=invalid_currency,
    )

    await requester.make_request(SendMessage, Update(update_id=1, message=msg))

    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.invalid_budget_currency)

    state = await requester.get_fsm_state()
    assert state == UpdateUser.budget_currency

    data = await requester.get_fsm_state_data()
    assert "budget_currency" not in data


@pytest.mark.asyncio
async def test_reset_currency(create_test_data, requester):
    await requester.set_fsm_state(UpdateUser.budget_currency)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=CurrencyUpdateData(action="reset").pack(),
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
    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.budget_currency_description)

    state = await requester.get_fsm_state()
    assert state == UpdateUser.budget_currency

    data = await requester.get_fsm_state_data()
    assert data.get("budget_currency") is None


@pytest.mark.asyncio
async def test_confirm_updated_currency(
    create_test_data, requester, persistent_db_session
):
    valid_currency = "valid"
    repo = UserRepository(persistent_db_session)
    db_user = repo.get_user(user_id=TARGET_USER_ID)
    assert db_user.budget_currency != valid_currency

    await requester.set_fsm_state(UpdateUser.budget_currency)
    await requester.update_fsm_state_data(budget_currency=valid_currency)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=CurrencyUpdateData(action="confirm").pack(),
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
    answer = requester.read_last_sent_message()
    assert_uses_template(
        answer,
        func.show_currency_update_summary,
        budget_currency=valid_currency,
    )

    persistent_db_session.refresh(db_user)
    assert db_user.budget_currency == valid_currency

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_activate_user(create_test_data, requester, repository):
    db_user = repository.get_user(user_id=TARGET_USER_ID)
    assert db_user.is_active is True
    del db_user

    repository.update_user(TARGET_USER_ID, is_active=False)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=sc.ACTIVATE_USER,
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
    answer = requester.read_last_sent_message()
    assert_uses_template(answer, const.user_activation_summary)

    db_user = repository.get_user(user_id=TARGET_USER_ID)
    assert db_user.is_active is True
