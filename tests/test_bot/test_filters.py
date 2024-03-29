import re

import pytest

from app.bot import string_constants as sc
from app.bot.filters import (
    BudgetCurrencyFilter,
    CategoryIdFIlter,
    CategoryNameFilter,
    CategoryTypeFilter,
    EntrySumFilter,
    SelectCategoryPageFilter,
    patterns,
)
from app.db.models import CategoryType
from app.exceptions import (
    InvalidBudgetCurrency,
    InvalidCallbackData,
    InvalidCategoryName,
    InvalidEntrySum,
)

from .conftest import generic_callback_query as callback
from .conftest import generic_message as msg

callback_data_mismatch = callback(data="callback_mismatch")


@pytest.mark.asyncio
async def test_category_type_filter():
    expenses = callback(data=f"{sc.SELECT_CATEGORY_TYPE}:expenses")
    income = callback(data=f"{sc.SELECT_CATEGORY_TYPE}:income")
    invalid = callback(data=f"{sc.SELECT_CATEGORY_TYPE}:invalid")

    context = await CategoryTypeFilter(expenses)
    assert context == {"category_type": CategoryType.EXPENSES}

    context = await CategoryTypeFilter(income)
    assert context == {"category_type": CategoryType.INCOME}

    with pytest.raises(InvalidCallbackData) as exc_info:
        context = await CategoryTypeFilter(invalid)
    assert exc_info.errisinstance(InvalidCallbackData)
    prefix = CategoryTypeFilter.callback_prefix
    suffix = CategoryTypeFilter._get_callback_suffix(invalid)
    assert str(exc_info.value) == str(
        InvalidCallbackData(f"callback_prefix={prefix}, suffix={suffix}")
    )

    assert await CategoryTypeFilter(callback_data_mismatch) is False


@pytest.mark.asyncio
async def test_category_id_filter():
    valid = callback(data=f"{sc.CATEGORY_ID}:11")
    invalid = callback(data=f"{sc.CATEGORY_ID}:eleven")

    context = await CategoryIdFIlter(valid)
    assert context == {"category_id": int(valid.data[-2:])}

    with pytest.raises(InvalidCallbackData) as exc_info:
        context = await CategoryIdFIlter(invalid)
    assert exc_info.errisinstance(InvalidCallbackData)
    prefix = CategoryIdFIlter.callback_prefix
    suffix = CategoryIdFIlter._get_callback_suffix(invalid)
    assert str(exc_info.value) == str(
        InvalidCallbackData(f"callback_prefix={prefix}, suffix={suffix}")
    )

    assert await CategoryTypeFilter(callback_data_mismatch) is False


@pytest.mark.asyncio
async def test_select_category_page_filter():
    next = callback(data=f"{sc.PAGINATED_CATEGORIES_PAGE}:next")
    prev = callback(data=f"{sc.PAGINATED_CATEGORIES_PAGE}:previous")
    invalid = callback(data=f"{sc.PAGINATED_CATEGORIES_PAGE}:invalid")

    context = await SelectCategoryPageFilter(next)
    assert context == {"switch_to_page": "next"}

    context = await SelectCategoryPageFilter(prev)
    assert context == {"switch_to_page": "previous"}

    with pytest.raises(InvalidCallbackData) as exc_info:
        context = await SelectCategoryPageFilter(invalid)
    assert exc_info.errisinstance(InvalidCallbackData)
    prefix = SelectCategoryPageFilter.callback_prefix
    suffix = SelectCategoryPageFilter._get_callback_suffix(invalid)
    assert str(exc_info.value) == str(
        InvalidCallbackData(f"callback_prefix={prefix}, suffix={suffix}")
    )

    assert await SelectCategoryPageFilter(callback_data_mismatch) is False


@pytest.mark.parametrize(
    "valid_currency",
    (
        "RUB",
        "rubles",
        "Rub",
        "руб",
        "РУБ",
        "рубли",
        "долл",
        "доллары",
        "зайчики",
        "rabBiTs",
    ),
)
@pytest.mark.asyncio
async def test_valid_budget_currency(valid_currency):
    assert await BudgetCurrencyFilter(msg(text=valid_currency)) == {
        "budget_currency": valid_currency
    }


@pytest.mark.parametrize(
    "invalid_currency",
    (
        "ToLongBudgetCurrency",
        "a spaced",
        "$pecial",
        "dash-name",
        "332323",
        "..doted..",
        "/slashed",
        "@!ff#",
    ),
)
@pytest.mark.asyncio
async def test_invalid_budget_currency(invalid_currency):
    pattern = patterns["budget_currency"]
    err_msg = f"Budget currency should follow pattern: {re.escape(pattern)}"
    with pytest.raises(InvalidBudgetCurrency, match=err_msg):
        await BudgetCurrencyFilter(msg(text=invalid_currency))


@pytest.mark.parametrize(
    "category_name",
    (
        "products",
        "Grocery",
        "favorite_coffe",
        "birthday21",
        "Кредит(Новобанк)",
        "На_пенсию,отдых",
        "блаГотвОрительность,лимитНаМес",
        "пост",
    ),
)
@pytest.mark.asyncio
async def test_valid_category_name(category_name):
    assert await CategoryNameFilter(msg(text=category_name)) == {
        "category_name": category_name
    }


@pytest.mark.parametrize(
    "category_name",
    (
        "ToLongCategoryNameWhichTakesMoreThan30Chars",
        "a",
        "aa",
        "aaa",
        "$pecial",
        "dash-name",
        "..doted..",
        "/slashed",
        "@!ff#",
    ),
)
@pytest.mark.asyncio
async def test_invalid_category_name(category_name):
    with pytest.raises(InvalidCategoryName):
        await CategoryNameFilter(msg(text=category_name))


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
    pattern = patterns["entry_sum"]
    err_msg = f"Entry sum should follow pattern: {re.escape(pattern)}"
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
