import re
from datetime import datetime
from functools import partial

import pytest
from aiogram.types import CallbackQuery, Message

from app.bot.filters import (
    CategoryIdFIlter,
    CategoryTypeFilter,
    EntrySumFilter,
    SelectCategoryPageFilter,
    entry_sum_pattern,
)
from app.db.models import CategoryType
from app.exceptions import InvalidCallbackData, InvalidEntrySum

from .conftest import chat, user

select_expenses_category_type = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="select_category_type_expenses",
    message=Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="Расходы",
    ),
)
select_income_category_type = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="select_category_type_income",
    message=Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="Доходы",
    ),
)
select_invalid_category_type = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="select_category_type_invalid",
    message=Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="Invalid",
    ),
)
valid_category_id = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="category_id_11",
    message=Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="message",
    ),
)
invalid_category_id = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="category_id_eleven",
    message=Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="message",
    ),
)
select_next_category_page = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="show_categories_page_next",
    message=Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="message",
    ),
)
select_previous_category_page = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="show_categories_page_previous",
    message=Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="message",
    ),
)
select_invalid_category_page = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="show_categories_page_invalid",
    message=Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="message",
    ),
)
callback_data_mismatch = CallbackQuery(
    id="12345678",
    from_user=user,
    chat_instance="AABBCC",
    data="callback_mismatch",
    message=Message(
        message_id=1,
        date=datetime.now(),
        from_user=user,
        chat=chat,
        text="Invalid",
    ),
)
msg = partial(
    Message, message_id=1, date=datetime.now(), from_user=user, chat=chat
)


@pytest.mark.asyncio
async def test_category_type_filter():
    context = await CategoryTypeFilter(select_expenses_category_type)
    assert context == {"category_type": CategoryType.EXPENSES}

    context = await CategoryTypeFilter(select_income_category_type)
    assert context == {"category_type": CategoryType.INCOME}

    with pytest.raises(InvalidCallbackData) as exc_info:
        context = await CategoryTypeFilter(select_invalid_category_type)
    assert exc_info.errisinstance(InvalidCallbackData)
    prefix = CategoryTypeFilter.callback_prefix
    suffix = CategoryTypeFilter._get_callback_suffix(
        select_invalid_category_type
    )
    assert str(exc_info.value) == str(
        InvalidCallbackData(f"callback_prefix={prefix}, suffix={suffix}")
    )

    assert await CategoryTypeFilter(callback_data_mismatch) is False


@pytest.mark.asyncio
async def test_category_id_filter():
    context = await CategoryIdFIlter(valid_category_id)
    assert context == {"category_id": int(valid_category_id.data[-2:])}

    with pytest.raises(InvalidCallbackData) as exc_info:
        context = await CategoryIdFIlter(invalid_category_id)
    assert exc_info.errisinstance(InvalidCallbackData)
    prefix = CategoryIdFIlter.callback_prefix
    suffix = CategoryIdFIlter._get_callback_suffix(invalid_category_id)
    assert str(exc_info.value) == str(
        InvalidCallbackData(f"callback_prefix={prefix}, suffix={suffix}")
    )

    assert await CategoryTypeFilter(callback_data_mismatch) is False


@pytest.mark.asyncio
async def test_select_category_page_filter():
    context = await SelectCategoryPageFilter(select_next_category_page)
    assert context == {"switch_to_page": "next"}

    context = await SelectCategoryPageFilter(select_previous_category_page)
    assert context == {"switch_to_page": "previous"}

    with pytest.raises(InvalidCallbackData) as exc_info:
        context = await SelectCategoryPageFilter(select_invalid_category_page)
    assert exc_info.errisinstance(InvalidCallbackData)
    prefix = SelectCategoryPageFilter.callback_prefix
    suffix = SelectCategoryPageFilter._get_callback_suffix(
        select_invalid_category_page
    )
    assert str(exc_info.value) == str(
        InvalidCallbackData(f"callback_prefix={prefix}, suffix={suffix}")
    )

    assert await SelectCategoryPageFilter(callback_data_mismatch) is False


@pytest.mark.parametrize(
    "input_num, output_num",
    [
        ("12", 1200),
        ("100.00", 10000),
        ("1.00", 100),
        ("0.1", 10),
        ("0.01", 1),
        ("10000.1", 1000010),
        ("388184.9", 38818490),
    ],
)
@pytest.mark.asyncio
async def test_valid_entry_sum(input_num, output_num):
    assert await EntrySumFilter(msg(text=input_num)) == {
        "entry_sum": output_num
    }


@pytest.mark.parametrize(
    "invalid_num",
    (
        "12,10",
        "0,1",
        "1231231231231994844342312312313",
        "11323.O",
        "forty_two",
        "3775.23938",
    ),
)
@pytest.mark.asyncio
async def test_invalid_entry_sum(invalid_num):
    err_msg = (
        f"Entry sum should follow pattern: {re.escape(entry_sum_pattern)}"
    )
    with pytest.raises(InvalidEntrySum, match=err_msg):
        await EntrySumFilter(msg(text=invalid_num))


@pytest.mark.parametrize(
    "zero",
    (
        "0",
        "00",
        "0.0",
        "0.00",
    ),
)
@pytest.mark.asyncio
async def test_zero_entry_sum(zero):
    err_msg = "Entry sum must be > 0!"
    with pytest.raises(InvalidEntrySum, match=err_msg):
        await EntrySumFilter(msg(text=zero))
