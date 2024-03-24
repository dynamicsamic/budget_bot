import re
from datetime import datetime
from typing import Any, Callable, Type, Union

from aiogram.filters import BaseFilter, Filter
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message

from app import settings
from app.bot import string_constants as sc
from app.custom_types import _MatchFnReturnDict
from app.db.models import CategoryType
from app.exceptions import (
    BotException,
    InvalidBudgetCurrency,
    InvalidCallbackData,
    InvalidCategoryName,
    InvalidEntrySum,
)
from app.utils import validate_entry_date

entry_sum_pattern = "[0-9]{1,18}[.]?[0-9]{0,2}"


def get_suffix(string: str) -> str:
    *_, suffix = string.rsplit("_", maxsplit=1)
    return suffix


class CallbackQueryFilter(Filter):
    def __init__(
        self,
        callback_prefix: str,
        get_context: Callable[[str], dict[str, Any] | None],
    ) -> None:
        self.callback_prefix = callback_prefix
        self.get_context = get_context

    async def __call__(self, callback: CallbackQuery) -> dict[str, Any] | bool:
        if suffix := self._get_callback_suffix(callback):
            if (callback_context := self.get_context(suffix)) is None:
                raise InvalidCallbackData(
                    f"callback_prefix={self.callback_prefix}, suffix={suffix}"
                )
            return callback_context

        return False

    def _get_callback_suffix(self, callback: CallbackQuery) -> str | None:
        *body, suffix = callback.data.split(f"{self.callback_prefix}:")
        if body == []:
            return

        return suffix


class MatchMessageFilter(Filter):
    def __init__(
        self,
        match_fn: Callable[[str], _MatchFnReturnDict],
        exc_type: Type[BotException],
    ) -> None:
        self.match_fn = match_fn
        self.exc_type = exc_type

    async def __call__(self, message: Message) -> dict[str, Any]:
        context, err_msg = self.match_fn(message.text).values()
        if err_msg:
            raise self.exc_type(err_msg)
        return context


class PatternMatchMessageFilter(Filter):
    def __init__(
        self,
        pattern: str,
        return_argname: str,
        exception_type: Type[Exception],
    ):
        self.pattern = pattern
        self.return_argname = return_argname
        self.exception_type = exception_type

    async def __call__(self, message: Message) -> dict[str, str]:
        if re.match(self.pattern, message.text):
            return {self.return_argname: message.text}
        raise self.exception_type(
            f"{self.return_argname} does not match pattern {self.pattern}"
        )


def get_category_type(category_type: str) -> dict[str, CategoryType] | None:
    if category_type == "income":
        return {"category_type": CategoryType.INCOME}
    elif category_type == "expenses":
        return {"category_type": CategoryType.EXPENSES}
    return


def get_next_category_page(switch_to_page: str) -> dict[str, str] | None:
    if switch_to_page in ("next", "previous"):
        return {"switch_to_page": switch_to_page}
    return


def get_category_id(category_id: str) -> dict[str, int] | None:
    if category_id.isdecimal():
        return {"category_id": int(category_id)}
    return


def match_entry_sum(entry_sum: str) -> _MatchFnReturnDict:
    result = {"context": None, "error": None}

    if re.fullmatch(entry_sum_pattern, entry_sum):
        candidate = int(round(float(entry_sum), 2) * 100)
        if candidate == 0:
            result["error"] = "Entry sum must be > 0!"
        else:
            result["context"] = {"entry_sum": candidate}
    else:
        result["error"] = (
            f"Entry sum should follow pattern: {entry_sum_pattern}"
        )

    return result


BudgetCurrencyFilter = PatternMatchMessageFilter(
    pattern=r"^[A-Za-zА-Яа-я]{3,10}$",
    return_argname="budget_currency",
    exception_type=InvalidBudgetCurrency,
)

CategoryNameFilter = PatternMatchMessageFilter(
    pattern=r"^[A-Za-zА-Яа-я0-9_,()]{4,30}$",
    return_argname="category_name",
    exception_type=InvalidCategoryName,
)
CategoryTypeFilter = CallbackQueryFilter(
    sc.SELECT_CATEGORY_TYPE, get_category_type
)
CategoryIdFIlter = CallbackQueryFilter(sc.CATEGORY_ID, get_category_id)
SelectCategoryPageFilter = CallbackQueryFilter(
    sc.PAGINATED_CATEGORIES_PAGE, get_next_category_page
)
CategoryDeleteConfirmFilter = CallbackQueryFilter(
    sc.DELETE_CATEGORY, get_category_id
)
EntryCategoryIdFilter = CallbackQueryFilter(
    sc.ENTRY_CATEGORY_ID, get_category_id
)
EntryCategoryPageFilter = CallbackQueryFilter(
    sc.ENTRY_CATEGORY_PAGE, get_next_category_page
)
EntrySumFilter = MatchMessageFilter(match_entry_sum, InvalidEntrySum)


class GetEntryId(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, int], bool]:
        if callback.data.startswith("entry_id"):
            entry_id = get_suffix(callback.data)
            return {"entry_id": int(entry_id)}
        return False


class EntryBudgetIdFilter(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, int], bool]:
        if callback.data.startswith("entry_budget_item"):
            budget_id = get_suffix(callback.data)
            return {"budget_id": int(budget_id)}
        return False


class EntryDateFilter(BaseFilter):
    async def __call__(
        self, message: Message
    ) -> dict[str, Union[datetime | None, str]]:
        if message.text == ".":
            transaction_date = message.date.astimezone(settings.TIME_ZONE)
            return {
                "transaction_date": transaction_date,
                "error_message": "",
            }

        transaction_date, error_message = validate_entry_date(message.text)
        return {
            "transaction_date": transaction_date,
            "error_message": error_message,
        }


class UserSignupData(CallbackData, prefix=sc.SIGNUP_USER):
    action: str


class CurrencyUpdateData(CallbackData, prefix=sc.UPDATE_CURRENCY):
    action: str


class ReportTypeData(CallbackData, prefix="report"):
    type: str
    period: str


class CategoryItemActionData(CallbackData, prefix="category_action"):
    action: str
    category_id: int


class UpdateCategoryChooseAttrData(CallbackData, prefix=sc.UPDATE_CATEGORY):
    attribute: str


class EntryItemActionData(CallbackData, prefix="action_entry_item"):
    entry_id: str
    action: str
