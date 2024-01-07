from datetime import datetime

import pytest
from aiogram.enums import ChatType
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User

from app.bot import keyboards, prompts
from app.bot.states import CreateCategory

from ..test_utils import clear_dispatcher_state, get_dispatcher_state

user = User(id=101, is_bot=False, first_name="User", username="username")
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
anonymous_user = User(
    id=999, is_bot=False, first_name="anonymous", username="anonymous"
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
