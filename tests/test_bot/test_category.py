from datetime import datetime

import pytest
from aiogram.enums import ChatType
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from app.bot import string_constants as sc
from app.bot.filters import CategoryItemActionData
from app.bot.states import CreateCategory, ShowCategories, UpdateCategory
from app.bot.templates import buttons, const, func, keyboards, texts
from app.db.models import CategoryType
from app.db.repository import CategoryRepository
from app.exceptions import ModelInstanceDuplicateAttempt
from app.utils import OffsetPaginator

from ..test_utils import CATEGORY_SAMPLE, TARGET_CATEGORY_ID, TARGET_USER_ID
from .conftest import chat, second_chat, second_user, user

create_category_command = Message(
    message_id=1,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text=f"/{sc.CREATE_CATEGORY_COMMAND}",
)
press_cancel_callback = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data=buttons.cancel_operation.callback_data,
    message=Message(
        message_id=2,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text=buttons.cancel_operation.text,
    ),
)
valid_category_name = Message(
    message_id=2,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text="salary",
)
valid_income_category_type = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data=f"{sc.SELECT_CATEGORY_TYPE}:income",
    message=Message(
        message_id=4,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="Доходы",
    ),
)
show_categories_command = Message(
    message_id=5,
    date=datetime.now(),
    from_user=user,
    chat=chat,
    text=f"/{sc.SHOW_CATEGORIES_COMMAND}",
)
show_next_categories_callback = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data=f"{sc.PAGINATED_CATEGORIES_PAGE}:next",
    message=Message(
        message_id=6,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="Следующие",
    ),
)
show_previous_categories_callback = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data=f"{sc.PAGINATED_CATEGORIES_PAGE}:previous",
    message=Message(
        message_id=7,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="Предыдущие",
    ),
)
show_invalid_categories_page_callback = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data=f"{sc.PAGINATED_CATEGORIES_PAGE}:invalid",
    message=Message(
        message_id=7,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="Предыдущие",
    ),
)
delete_category = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data=CategoryItemActionData(
        action="delete", category_id=TARGET_CATEGORY_ID
    ).pack(),
    message=Message(
        message_id=10,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="just_message",
    ),
)
delete_category_confirm = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data=buttons.confirm_delete_category(TARGET_CATEGORY_ID).callback_data,
    message=Message(
        message_id=11,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="just_message",
    ),
)


@pytest.mark.asyncio
async def test_category_handlers_redirect_anonymous_user(
    create_test_data, requester
):
    anonymous_user = User(
        id=999, is_bot=False, first_name="anon", username="anon"
    )
    anonymous_chat = Chat(id=999, type=ChatType.PRIVATE)
    msg = create_category_command.model_copy(
        update={"from_user": anonymous_user, "chat": anonymous_chat}
    )
    await requester.make_request(
        SendMessage,
        Update(update_id=1, message=msg),
    )
    text, markup = const.redirect_anonymous.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup


@pytest.mark.asyncio
async def test_create_category_command(create_test_data, requester):
    await requester.make_request(
        SendMessage,
        Update(
            update_id=1,
            message=create_category_command,
        ),
    )

    message = requester.read_last_sent_message()
    text, markup = const.category_name_description.values()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state == CreateCategory.set_name


@pytest.mark.asyncio
async def test_create_category_command_press_cancel_button(
    create_test_data, requester
):
    await requester.make_request(
        SendMessage,
        Update(
            update_id=1,
            message=create_category_command,
        ),
    )


@pytest.mark.asyncio
async def test_create_category_set_valid_name(create_test_data, requester):
    ################ test setup ##################
    await requester.set_fsm_state(CreateCategory.set_name)
    ##############################################

    await requester.make_request(
        SendMessage,
        Update(
            update_id=1,
            message=valid_category_name,
        ),
    )

    text, markup = const.category_type_selection.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state == CreateCategory.set_type

    state_data = await requester.get_fsm_state_data()
    assert state_data == {"category_name": valid_category_name.text}


@pytest.mark.asyncio
async def test_create_category_set_invalid_name(create_test_data, requester):
    ################ test setup ##################
    await requester.set_fsm_state(CreateCategory.set_name)
    ##############################################

    invalid_category_name = Message(
        message_id=2,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="$alary",
    )

    await requester.make_request(
        SendMessage,
        Update(
            update_id=1,
            message=invalid_category_name,
        ),
    )

    text, markup = const.invalid_category_name.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state == CreateCategory.set_name

    state_data = await requester.get_fsm_state_data()
    assert "category_name" not in state_data


@pytest.mark.asyncio
async def test_create_category_set_existing_name(create_test_data, requester):
    ################ test setup ##################
    await requester.set_fsm_state(CreateCategory.set_name)
    ##############################################

    existing_category_name = Message(
        message_id=2,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="category1",
    )

    await requester.make_request(
        SendMessage,
        Update(
            update_id=1,
            message=existing_category_name,
        ),
    )

    exception = ModelInstanceDuplicateAttempt(
        user_tg_id=user.id,
        model_name="Категория",
        duplicate_arg_name="Название",
        duplicate_arg_value=existing_category_name.text,
    )
    text, markup = const.instance_duplicate_attempt(exception).values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state == CreateCategory.set_name

    state_data = await requester.get_fsm_state_data()
    assert "category_name" not in state_data


@pytest.mark.asyncio
async def test_create_category_set_valid_income_type_and_finish(
    create_test_data, requester, persistent_db_session
):
    ################ test setup ##################
    await requester.update_fsm_state_data(
        category_name=valid_category_name.text
    )
    await requester.set_fsm_state(CreateCategory.set_type)
    ##############################################

    repository = CategoryRepository(persistent_db_session)
    initial_category_count = repository.count_user_categories(TARGET_USER_ID)

    await requester.make_request(
        AnswerCallbackQuery,
        Update(
            update_id=1,
            callback_query=valid_income_category_type,
        ),
    )

    current_category_count = repository.count_user_categories(TARGET_USER_ID)
    assert current_category_count == initial_category_count + 1

    created_category = repository.get_category(CATEGORY_SAMPLE + 1)
    assert created_category.name == valid_category_name.text
    assert created_category.type.description == "Доходы"
    assert created_category.user_id == TARGET_USER_ID

    text, markup = func.show_category_create_summary(created_category).values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_create_category_set_valid_expenses_type_and_finish(
    create_test_data, requester, persistent_db_session
):
    ################ test setup ##################
    await requester.update_fsm_state_data(
        category_name=valid_category_name.text
    )
    await requester.set_fsm_state(CreateCategory.set_type)
    ##############################################

    repository = CategoryRepository(persistent_db_session)
    initial_category_count = repository.count_user_categories(TARGET_USER_ID)

    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.SELECT_CATEGORY_TYPE}:expenses",
        message=Message(
            message_id=4,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="Расходы",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(
            update_id=1,
            callback_query=callback,
        ),
    )

    current_category_count = repository.count_user_categories(TARGET_USER_ID)
    assert current_category_count == initial_category_count + 1

    created_category = repository.get_category(CATEGORY_SAMPLE + 1)
    assert created_category.name == valid_category_name.text
    assert created_category.type.description == "Расходы"
    assert created_category.user_id == TARGET_USER_ID

    text, markup = func.show_category_create_summary(created_category).values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_create_category_set_invalid_type_and_finish(
    create_test_data, requester, persistent_db_session
):
    ################ test setup ##################
    await requester.update_fsm_state_data(
        category_name=valid_category_name.text
    )
    await requester.set_fsm_state(CreateCategory.set_type)
    ##############################################

    repository = CategoryRepository(persistent_db_session)
    initial_category_count = repository.count_user_categories(TARGET_USER_ID)

    invalid_type_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.SELECT_CATEGORY_TYPE}:invalid",
        message=Message(
            message_id=4,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="invalid",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(
            update_id=1,
            callback_query=invalid_type_callback,
        ),
    )

    current_category_count = repository.count_user_categories(TARGET_USER_ID)
    assert current_category_count == initial_category_count

    text, markup = const.serverside_error.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_create_category_set_type_finish_invalid_name(
    create_test_data, requester, persistent_db_session
):
    ################ test setup ##################
    # intentionally inject a bug, category_name must be a valid str
    await requester.update_fsm_state_data(category_name=25)
    await requester.set_fsm_state(CreateCategory.set_type)
    ##############################################

    repository = CategoryRepository(persistent_db_session)
    initial_category_count = repository.count_user_categories(TARGET_USER_ID)

    await requester.make_request(
        AnswerCallbackQuery,
        Update(
            update_id=1,
            callback_query=valid_income_category_type,
        ),
    )

    current_category_count = repository.count_user_categories(TARGET_USER_ID)
    assert current_category_count == initial_category_count

    text, markup = const.serverside_error.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_create_category_callback(create_test_data, requester):
    callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data="create_category",
        message=Message(
            message_id=1,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text=buttons.create_category.text,
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=callback),
    )

    text, markup = const.category_name_description.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state == CreateCategory.set_name


@pytest.mark.asyncio
async def test_show_categories_command_with_zero_categories(
    create_test_data, requester
):
    msg = show_categories_command.model_copy(
        update={"from_user": second_user, "chat": second_chat}
    )
    await requester.make_request(
        SendMessage,
        Update(update_id=1, message=msg),
    )

    text, markup = const.zero_category.values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_show_categories_command(
    create_test_data, requester, persistent_db_session
):
    await requester.make_request(
        SendMessage,
        Update(update_id=1, message=show_categories_command),
    )

    page_limit = 5
    paginator = OffsetPaginator(
        sc.PAGINATED_CATEGORIES_PAGE, CATEGORY_SAMPLE, page_limit
    )
    categories = CategoryRepository(persistent_db_session).get_user_categories(
        TARGET_USER_ID
    )

    text, markup = func.show_paginated_categories(
        categories.result, paginator
    ).values()
    message = requester.read_last_sent_message()
    assert message.text == text
    assert message.reply_markup == markup

    state = await requester.get_fsm_state()
    assert state == ShowCategories.show_many

    state_data = await requester.get_fsm_state_data()
    assert state_data == {"paginator": paginator}

    kb = message.reply_markup.model_dump().get("inline_keyboard")
    for button, i in zip(kb, range(1, page_limit + 1)):
        assert button[0]["callback_data"] == f"category_id:{i}"

    next_button = kb[-1][0]
    assert next_button["text"] == "Следующие"
    assert next_button["callback_data"] == f"{paginator.callback_prefix}:next"

    assert all(button[0]["text"] != "Предыдущие" for button in kb)
    assert all(
        button[0]["callback_data"] != f"{paginator.callback_prefix}:previous"
        for button in kb
    )


@pytest.mark.asyncio
async def test_show_categories_next_page(
    create_test_data, requester, persistent_db_session
):
    await requester.make_request(
        SendMessage,
        Update(update_id=1, message=show_categories_command),
    )
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=2, callback_query=show_next_categories_callback),
    )

    page_limit = 5
    paginator = OffsetPaginator(
        sc.PAGINATED_CATEGORIES_PAGE, CATEGORY_SAMPLE, page_limit
    )
    paginator.switch_next()
    categories = CategoryRepository(persistent_db_session).get_user_categories(
        TARGET_USER_ID, offset=paginator.current_offset
    )

    message = requester.read_last_sent_message()
    expected_text = texts.category_choose_action
    expected_markup = keyboards.base.paginated_category_item_list(
        categories.result, paginator
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == ShowCategories.show_many

    state_data = await requester.get_fsm_state_data()
    assert state_data == {"paginator": paginator}

    kb = message.reply_markup.model_dump().get("inline_keyboard")
    for button, i in zip(
        kb,
        range(
            paginator.current_offset + 1,
            paginator.current_offset + page_limit + 1,
        ),
    ):
        assert button[0]["callback_data"] == f"category_id:{i}"

    next_button = kb[-1][0]
    assert next_button["text"] == "Следующие"
    assert next_button["callback_data"] == f"{paginator.callback_prefix}:next"

    previous_button = kb[-2][0]
    assert previous_button["text"] == "Предыдущие"
    assert (
        previous_button["callback_data"]
        == f"{paginator.callback_prefix}:previous"
    )


@pytest.mark.asyncio
async def test_show_categories_last_page(
    create_test_data, requester, persistent_db_session
):
    await requester.make_request(
        SendMessage,
        Update(update_id=1, message=show_categories_command),
    )
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=2, callback_query=show_next_categories_callback),
    )
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=3, callback_query=show_next_categories_callback),
    )
    page_limit = 5
    paginator = OffsetPaginator(
        sc.PAGINATED_CATEGORIES_PAGE, CATEGORY_SAMPLE, page_limit
    )
    paginator.switch_next()
    paginator.switch_next()
    categories = CategoryRepository(persistent_db_session).get_user_categories(
        TARGET_USER_ID, offset=paginator.current_offset
    )

    message = requester.read_last_sent_message()
    expected_text = texts.category_choose_action
    expected_markup = keyboards.base.paginated_category_item_list(
        categories.result, paginator
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == ShowCategories.show_many

    state_data = await requester.get_fsm_state_data()
    assert state_data == {"paginator": paginator}

    kb = message.reply_markup.model_dump().get("inline_keyboard")
    for button, i in zip(
        kb,
        range(
            paginator.current_offset + 1,
            paginator.current_offset + page_limit + 1,
        ),
    ):
        assert button[0]["callback_data"] == f"category_id:{i}"

    previous_button = kb[-1][0]
    assert previous_button["text"] == "Предыдущие"
    assert (
        previous_button["callback_data"]
        == f"{paginator.callback_prefix}:previous"
    )

    assert all(button[0]["text"] != "Следующие" for button in kb)
    assert all(
        button[0]["callback_data"] != f"{paginator.callback_prefix}:next"
        for button in kb
    )


@pytest.mark.asyncio
async def test_show_categories_previous_page(
    create_test_data, requester, persistent_db_session
):
    await requester.make_request(
        SendMessage,
        Update(update_id=1, message=show_categories_command),
    )
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=2, callback_query=show_next_categories_callback),
    )
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=3, callback_query=show_previous_categories_callback),
    )

    page_limit = 5
    paginator = OffsetPaginator(
        sc.PAGINATED_CATEGORIES_PAGE, CATEGORY_SAMPLE, page_limit
    )
    categories = CategoryRepository(persistent_db_session).get_user_categories(
        TARGET_USER_ID
    )
    message = requester.read_last_sent_message()
    expected_text = texts.category_choose_action
    expected_markup = keyboards.base.paginated_category_item_list(
        categories.result, paginator
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == ShowCategories.show_many

    state_data = await requester.get_fsm_state_data()
    assert state_data == {"paginator": paginator}

    kb = message.reply_markup.model_dump().get("inline_keyboard")
    for button, i in zip(kb, range(1, page_limit + 1)):
        assert button[0]["callback_data"] == f"category_id:{i}"

    next_button = kb[-1][0]
    assert next_button["text"] == "Следующие"
    assert next_button["callback_data"] == f"{paginator.callback_prefix}:next"

    assert all(button[0]["text"] != "Предыдущие" for button in kb)
    assert all(
        button[0]["callback_data"] != f"{paginator.callback_prefix}:previous"
        for button in kb
    )


@pytest.mark.asyncio
async def test_show_categories_invalid_page(create_test_data, requester):
    await requester.make_request(
        SendMessage,
        Update(update_id=1, message=show_categories_command),
    )
    await requester.make_request(
        AnswerCallbackQuery,
        Update(
            update_id=2, callback_query=show_invalid_categories_page_callback
        ),
    )

    message = requester.read_last_sent_message()
    assert message.text == texts.serverside_error_response
    assert message.reply_markup is None

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_show_categories_callback(
    create_test_data, requester, persistent_db_session
):
    show_categories_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data="show_categories",
        message=Message(
            message_id=8,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text=buttons.show_categories.text,
        ),
    )
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=show_categories_callback),
    )

    page_limit = 5
    paginator = OffsetPaginator(
        sc.PAGINATED_CATEGORIES_PAGE, CATEGORY_SAMPLE, page_limit
    )
    categories = CategoryRepository(persistent_db_session).get_user_categories(
        TARGET_USER_ID
    )
    message = requester.read_last_sent_message()
    expected_text = texts.category_choose_action
    expected_markup = keyboards.base.paginated_category_item_list(
        categories.result, paginator
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == ShowCategories.show_many

    state_data = await requester.get_fsm_state_data()
    assert state_data == {"paginator": paginator}

    kb = message.reply_markup.model_dump().get("inline_keyboard")
    for button, i in zip(kb, range(1, page_limit + 1)):
        assert button[0]["callback_data"] == f"category_id:{i}"

    next_button = kb[-1][0]
    assert next_button["text"] == "Следующие"
    assert next_button["callback_data"] == f"{paginator.callback_prefix}:next"

    assert all(button[0]["text"] != "Предыдущие" for button in kb)
    assert all(
        button[0]["callback_data"] != f"{paginator.callback_prefix}:previous"
        for button in kb
    )


@pytest.mark.asyncio
async def test_show_category_control_options(create_test_data, requester):
    await requester.set_fsm_state(ShowCategories.show_many)
    control_options_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.CATEGORY_ID}:{TARGET_CATEGORY_ID}",
        message=Message(
            message_id=9,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=control_options_callback),
    )

    message = requester.read_last_sent_message()
    expected_text = "Выберите действие"
    expected_markup = keyboards.applied.category_item_choose_action(
        TARGET_CATEGORY_ID
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == ShowCategories.show_one

    kb = message.reply_markup.model_dump().get("inline_keyboard")

    update_button = kb[0][0]
    assert update_button["text"] == "Изменить"

    callback_data = CategoryItemActionData(
        action="update", category_id=TARGET_CATEGORY_ID
    )
    assert update_button["callback_data"] == callback_data.pack()


@pytest.mark.asyncio
async def test_show_category_control_options_invalid_type_id(
    create_test_data, requester
):
    await requester.set_fsm_state(ShowCategories.show_many)
    invalid_type_id_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.CATEGORY_ID}:invalid",
        message=Message(
            message_id=9,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(
            update_id=1,
            callback_query=invalid_type_id_callback,
        ),
    )
    message = requester.read_last_sent_message()
    assert message.text == texts.serverside_error_response
    assert message.reply_markup is None

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_delete_category_warn_user(
    persistent_db_session, create_test_data, requester
):
    ################ test setup ##################
    await requester.set_fsm_state(ShowCategories.show_one)
    ##############################################

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=2, callback_query=delete_category),
    )

    repository = CategoryRepository(persistent_db_session)
    category = repository.get_category(TARGET_CATEGORY_ID)
    entry_count = repository.count_category_entries(TARGET_CATEGORY_ID)

    message = requester.read_last_sent_message()
    expected_text = texts.show_delete_category_warning(
        category.name, entry_count
    )
    button_1 = buttons.switch_to_update_category(category.id)
    button_2 = buttons.confirm_delete_category(category.id)
    expected_markup = keyboards.base.button_menu(button_1, button_2)
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == ShowCategories.show_one

    state_data = await requester.get_fsm_state_data()
    assert state_data == {}

    kb = message.reply_markup.model_dump().get("inline_keyboard")

    cancel_button = kb[0][0]
    assert cancel_button["text"] == button_1.text
    assert cancel_button["callback_data"] == button_1.callback_data

    confirm_button = kb[1][0]
    assert confirm_button["text"] == button_2.text
    assert confirm_button["callback_data"] == button_2.callback_data


@pytest.mark.asyncio
async def test_category_delete_confirm(
    create_test_data, requester, persistent_db_session
):
    repository = CategoryRepository(persistent_db_session)
    initial_category_count = repository.count_user_categories(TARGET_USER_ID)
    initial_entry_count = repository.count_category_entries(TARGET_CATEGORY_ID)
    assert initial_entry_count > 0

    await requester.set_fsm_state(ShowCategories.show_one)
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=delete_category),
    )
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=2, callback_query=delete_category_confirm),
    )

    current_category_count = repository.count_user_categories(TARGET_USER_ID)
    current_entry_count = repository.count_category_entries(TARGET_CATEGORY_ID)
    assert current_category_count == initial_category_count - 1
    assert current_entry_count == 0

    message = requester.read_last_sent_message()
    expected_text = texts.confirm_category_deleted
    expected_markup = keyboards.base.button_menu(
        buttons.show_categories, buttons.main_menu
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state is None

    state_data = await requester.get_fsm_state_data()
    assert state_data == {}


@pytest.mark.asyncio
async def test_category_delete_switch_to_update(
    persistent_db_session, create_test_data, requester
):
    repository = CategoryRepository(persistent_db_session)
    initial_category_count = repository.count_user_categories(TARGET_USER_ID)
    initial_entry_count = repository.count_category_entries(TARGET_CATEGORY_ID)
    assert initial_entry_count > 0

    switch_to_update_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=buttons.switch_to_update_category(
            TARGET_CATEGORY_ID
        ).callback_data,
        message=Message(
            message_id=12,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.set_fsm_state(ShowCategories.show_one)
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=delete_category),
    )
    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=2, callback_query=switch_to_update_callback),
    )

    current_category_count = repository.count_user_categories(TARGET_USER_ID)
    current_entry_count = repository.count_category_entries(TARGET_CATEGORY_ID)
    assert current_category_count == initial_category_count
    assert current_entry_count == initial_entry_count

    message = requester.read_last_sent_message()
    expected_markup = keyboards.applied.category_update_options
    assert message.text == texts.update_category_invite_user
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == UpdateCategory.choose_attribute

    state_data = await requester.get_fsm_state_data()
    assert state_data == {"category_id": TARGET_CATEGORY_ID}


@pytest.mark.asyncio
async def test_update_category_choose_attribute(create_test_data, requester):
    ################ test setup ##################
    await requester.set_fsm_state(ShowCategories.show_one)
    ##############################################

    choose_attribute_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=CategoryItemActionData(
            action="update", category_id=TARGET_CATEGORY_ID
        ).pack(),
        message=Message(
            message_id=13,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=choose_attribute_callback),
    )

    message = requester.read_last_sent_message()
    expected_markup = keyboards.applied.category_update_options
    assert message.text == texts.update_category_invite_user
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == UpdateCategory.choose_attribute

    state_data = await requester.get_fsm_state_data()
    assert state_data == {"category_id": TARGET_CATEGORY_ID}


@pytest.mark.asyncio
async def test_update_category_request_name(create_test_data, requester):
    ################ test setup ##################
    await requester.set_fsm_state(UpdateCategory.choose_attribute)
    await requester.update_fsm_state_data(category_id=TARGET_CATEGORY_ID)
    ##############################################

    request_name_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.UPDATE_CATEGORY}:name",
        message=Message(
            message_id=13,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=request_name_callback),
    )

    message = requester.read_last_sent_message()
    expected_text = (
        "Введите новое название категории" f"{texts.category_name_description}"
    )
    expected_markup = keyboards.base.button_menu(
        buttons.cancel_operation, buttons.main_menu
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup


@pytest.mark.asyncio
async def test_update_category_set_name(
    persistent_db_session, create_test_data, requester
):
    ################ test setup ##################
    await requester.set_fsm_state(UpdateCategory.update_name)
    await requester.update_fsm_state_data(category_id=TARGET_CATEGORY_ID)
    ##############################################

    repository = CategoryRepository(persistent_db_session)
    initial_category_name = repository.get_category(TARGET_CATEGORY_ID).name

    valid_name_message = Message(
        message_id=13,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="updated_name",
    )

    await requester.make_request(
        SendMessage,
        Update(update_id=1, message=valid_name_message),
    )

    message = requester.read_last_sent_message()
    expected_text = texts.update_category_confirm_new_name.format(
        category_name=valid_name_message.text
    )
    expected_markup = keyboards.applied.category_update_options
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == UpdateCategory.choose_attribute

    current_category_name = repository.get_category(TARGET_CATEGORY_ID).name
    assert current_category_name != initial_category_name
    assert current_category_name == valid_name_message.text


@pytest.mark.asyncio
async def test_update_category_set_invalid_name(
    persistent_db_session, create_test_data, requester
):
    ################ test setup ##################
    await requester.set_fsm_state(UpdateCategory.update_name)
    await requester.update_fsm_state_data(category_id=TARGET_CATEGORY_ID)
    ##############################################

    repository = CategoryRepository(persistent_db_session)
    initial_category_name = repository.get_category(TARGET_CATEGORY_ID).name

    invalid_name_message = Message(
        message_id=13,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="/nvalid$",
    )

    await requester.make_request(
        SendMessage,
        Update(update_id=1, message=invalid_name_message),
    )

    message = requester.read_last_sent_message()
    expected_text = (
        "Недопустимое название категории." f"{texts.category_name_description}"
    )
    assert message.text == expected_text

    state = await requester.get_fsm_state()
    assert state == UpdateCategory.update_name

    current_category_name = repository.get_category(TARGET_CATEGORY_ID).name
    assert current_category_name == initial_category_name


@pytest.mark.asyncio
async def test_update_category_request_type(create_test_data, requester):
    ################ test setup ##################
    await requester.set_fsm_state(UpdateCategory.choose_attribute)
    await requester.update_fsm_state_data(category_id=TARGET_CATEGORY_ID)
    ##############################################

    request_type_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.UPDATE_CATEGORY}:type",
        message=Message(
            message_id=13,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=request_type_callback),
    )

    message = requester.read_last_sent_message()
    expected_text = "Выберите новый тип категории"
    expected_markup = keyboards.base.create_callback_buttons(
        button_names={"Доходы": "income", "Расходы": "expenses"},
        callback_prefix="select_category_type",
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == UpdateCategory.update_type


@pytest.mark.asyncio
async def test_update_category_set_income_type(
    persistent_db_session, create_test_data, requester
):
    ################ test setup ##################
    await requester.set_fsm_state(UpdateCategory.update_type)
    await requester.update_fsm_state_data(category_id=TARGET_CATEGORY_ID)
    ##############################################

    set_income_type_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.SELECT_CATEGORY_TYPE}:income",
        message=Message(
            message_id=13,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=set_income_type_callback),
    )

    repository = CategoryRepository(persistent_db_session)
    updated_category_type = repository.get_category(TARGET_CATEGORY_ID).type
    assert updated_category_type == CategoryType.INCOME

    message = requester.read_last_sent_message()
    expected_text = texts.update_category_confirm_new_type.format(
        category_type=CategoryType.INCOME.description
    )
    expected_markup = keyboards.applied.category_update_options
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == UpdateCategory.choose_attribute


@pytest.mark.asyncio
async def test_update_category_set_expenses_type(
    persistent_db_session, create_test_data, requester
):
    ################ test setup ##################
    await requester.set_fsm_state(UpdateCategory.update_type)
    await requester.update_fsm_state_data(category_id=TARGET_CATEGORY_ID)
    ##############################################

    set_expenses_type_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.SELECT_CATEGORY_TYPE}:expenses",
        message=Message(
            message_id=13,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=set_expenses_type_callback),
    )

    repository = CategoryRepository(persistent_db_session)
    updated_category_type = repository.get_category(TARGET_CATEGORY_ID).type
    assert updated_category_type == CategoryType.EXPENSES

    message = requester.read_last_sent_message()
    expected_text = texts.update_category_confirm_new_type.format(
        category_type=CategoryType.EXPENSES.description
    )
    expected_markup = keyboards.applied.category_update_options
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state == UpdateCategory.choose_attribute


@pytest.mark.asyncio
async def test_update_category_finish(
    persistent_db_session, create_test_data, requester
):
    ################ test setup ##################
    await requester.set_fsm_state(UpdateCategory.choose_attribute)
    await requester.update_fsm_state_data(category_id=TARGET_CATEGORY_ID)
    await requester.update_fsm_state_data(category_name="updated")
    ##############################################

    finish_category_update_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.UPDATE_CATEGORY}:finish",
        message=Message(
            message_id=13,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=finish_category_update_callback),
    )

    repository = CategoryRepository(persistent_db_session)
    category = repository.get_category(TARGET_CATEGORY_ID)

    message = requester.read_last_sent_message()
    expected_text = texts.show_update_summary(category)
    expected_markup = keyboards.base.button_menu(
        buttons.show_categories, buttons.main_menu
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state is None


@pytest.mark.asyncio
async def test_update_category_finish_without_changes(
    create_test_data, requester
):
    ################ test setup ##################
    await requester.set_fsm_state(UpdateCategory.choose_attribute)
    await requester.update_fsm_state_data(category_id=TARGET_CATEGORY_ID)
    ##############################################

    finish_category_update_callback = CallbackQuery(
        id="12345678",
        from_user=user,
        chat_instance="AABBCC",
        data=f"{sc.UPDATE_CATEGORY}:finish",
        message=Message(
            message_id=13,
            date=datetime.now(),
            from_user=user,
            chat=chat,
            text="just_message",
        ),
    )

    await requester.make_request(
        AnswerCallbackQuery,
        Update(update_id=1, callback_query=finish_category_update_callback),
    )

    message = requester.read_last_sent_message()
    expected_text = texts.update_without_changes
    expected_markup = keyboards.base.button_menu(
        buttons.show_categories, buttons.main_menu
    )
    assert message.text == expected_text
    assert message.reply_markup == expected_markup

    state = await requester.get_fsm_state()
    assert state is None
