from datetime import datetime

import pytest
from aiogram.enums import ChatType
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from app.bot import keyboards, prompts
from app.bot.states import CreateCategory
from app.db.repository import CategoryRepository

from ..test_utils import (
    CATEGORY_SAMPLE,
    TARGET_USER_ID,
    clear_dispatcher_state,
    get_dispatcher_state,
    get_dispatcher_state_data,
)

user = User(id=101, is_bot=False, first_name="User", username="username")
anonymous_user = User(
    id=999, is_bot=False, first_name="anonymous", username="anonymous"
)
chat = Chat(id=1, type=ChatType.PRIVATE)
create_category_command = Message(
    message_id=1,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text="/create_category",
)
valid_category_name = Message(
    message_id=2,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text="electronics",
)
invalid_category_name = Message(
    message_id=2,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text="&electronic$",
)
existing_category_name = Message(
    message_id=2,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text="category1",
)
valid_category_type = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="select_category_type_expenses",
    message=Message(
        message_id=4,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="Расходы",
    ),
)


@pytest.mark.asyncio
async def test_category_handlers_redirect_anonymous_user(
    create_test_data, mocked_bot, dispatcher
):
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    await dispatcher.feed_update(
        mocked_bot,
        Update(
            message=Message(
                message_id=1,
                date=datetime.now(),
                from_user=anonymous_user,
                chat=chat,
                text="/create_category",
            ),
            update_id=1,
        ),
    )
    message = mocked_bot.read_last_request()
    expected_text = (
        "Для работы с ботом, зарегистрируйтесь или активируйте Ваш аккаунт, "
        "выбрав одну из кнопок ниже."
    )
    expected_markup = keyboards.button_menu(
        keyboards.buttons.signup_user, keyboards.buttons.activate_user
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup


@pytest.mark.asyncio
async def test_cmd_create_category(create_test_data, mocked_bot, dispatcher):
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=create_category_command, update_id=1),
    )

    message = mocked_bot.read_last_request()
    expected_text = (
        "Введите название новой категории.\n"
        f"{prompts.category_name_description}"
    )
    expected_markup = keyboards.button_menu(
        keyboards.buttons.cancel_operation, keyboards.buttons.main_menu
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await get_dispatcher_state(dispatcher, mocked_bot, chat, user)
    assert state == CreateCategory.set_name

    await clear_dispatcher_state(dispatcher, mocked_bot, chat, user)


@pytest.mark.asyncio
async def test_create_category_set_name_with_valid_name(
    create_test_data, mocked_bot, dispatcher
):
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=create_category_command, update_id=1),
    )
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=valid_category_name, update_id=2),
    )

    message = mocked_bot.read_last_request()
    expected_text = "Выберите один из двух типов категорий"
    expected_markup = keyboards.create_callback_buttons(
        button_names={"Доходы": "income", "Расходы": "expenses"},
        callback_prefix="select_category_type",
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await get_dispatcher_state(dispatcher, mocked_bot, chat, user)
    assert state == CreateCategory.set_type

    state_data = await get_dispatcher_state_data(
        dispatcher, mocked_bot, chat, user
    )
    assert state_data == {"category_name": valid_category_name.text}

    await clear_dispatcher_state(dispatcher, mocked_bot, chat, user)


@pytest.mark.asyncio
async def test_create_category_set_name_with_invalid_name(
    create_test_data, mocked_bot, dispatcher
):
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=create_category_command, update_id=1),
    )
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=invalid_category_name, update_id=2),
    )

    message = mocked_bot.read_last_request()
    expected_text = (
        "Недопустимое название категории."
        f"{prompts.category_name_description}"
    )
    assert message.text == expected_text

    state = await get_dispatcher_state(dispatcher, mocked_bot, chat, user)
    assert state == CreateCategory.set_name

    await clear_dispatcher_state(dispatcher, mocked_bot, chat, user)


@pytest.mark.asyncio
async def test_create_category_set_name_with_existing_name(
    create_test_data, mocked_bot, dispatcher
):
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=create_category_command, update_id=1),
    )
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=existing_category_name, update_id=2),
    )

    message = mocked_bot.read_last_request()
    expected_text = (
        "У Вас уже есть категория с названием "
        f"{existing_category_name.text.capitalize()}.\n"
        "Пожалуйста, придумайте другое название для новой категории."
    )
    expected_markup = keyboards.button_menu(keyboards.buttons.cancel_operation)
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await get_dispatcher_state(dispatcher, mocked_bot, chat, user)
    assert state == CreateCategory.set_name

    await clear_dispatcher_state(dispatcher, mocked_bot, chat, user)


@pytest.mark.asyncio
async def test_create_category_set_type_and_finish_success(
    create_test_data, mocked_bot, dispatcher, persistent_db_session
):
    repository = CategoryRepository(persistent_db_session)
    initial_category_count = repository.count_user_categories(TARGET_USER_ID)

    mocked_bot.prepare_stub_messages(2)
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=create_category_command, update_id=1),
    )
    await dispatcher.feed_update(
        mocked_bot,
        Update(message=valid_category_name, update_id=2),
    )
    mocked_bot.add_result_for(method=AnswerCallbackQuery, ok=True)
    mocked_bot.add_result_for(method=SendMessage, ok=True)
    await dispatcher.feed_update(
        mocked_bot, Update(callback_query=valid_category_type, update_id=3)
    )

    current_category_count = repository.count_user_categories(TARGET_USER_ID)
    assert current_category_count == initial_category_count + 1
