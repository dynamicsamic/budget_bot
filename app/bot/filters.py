import re
from datetime import datetime
from typing import Any, Callable, Type, Union

from aiogram.filters import BaseFilter, Filter
from aiogram.types import CallbackQuery, Message

from app import settings
from app.db.models import CategoryType
from app.exceptions import InvalidCallbackData, InvalidCategoryName
from app.utils import validate_entry_date, validate_entry_sum


def get_suffix(string: str) -> str:
    *_, suffix = string.rsplit("_", maxsplit=1)
    return suffix


class BudgetNameFilter(BaseFilter):
    async def __call__(
        self, msg: Message | CallbackQuery
    ) -> dict[str, str | None]:
        user_input = (
            msg.text
            if isinstance(msg, Message)
            else CallbackQuery.message.text
        )

        context = {"filtered_budget_name": None}

        valid_name_pattern = r"^[A-Za-zА-Яа-я0-9-_]{4,25}$"
        if re.match(valid_name_pattern, user_input):
            context["filtered_budget_name"] = user_input

        return context


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
            callback_context = self.get_context(suffix)
            if callback_context is None:
                raise InvalidCallbackData(
                    f"callback_prefix={self.callback_prefix}, suffix={suffix}"
                )
            return callback_context

        return False

    def _get_callback_suffix(self, callback: CallbackQuery) -> str | None:
        *body, suffix = callback.data.split(f"{self.callback_prefix}_")
        if body == []:
            return

        return suffix


class PatternMatchMessageFilter(Filter):
    def __init__(
        self, pattern, return_argname: str, exception_type: Type[Exception]
    ):
        self.pattern = pattern
        self.return_argname = return_argname
        self.exception_type = exception_type

    async def __call__(self, message: Message) -> dict[str, str]:
        if re.match(self.pattern, message.text):
            return {self.return_argname: message.text.casefold()}
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


def get_confirm_or_cancel(confirm_or_cancel: str) -> dict[str, int] | None:
    if confirm_or_cancel in ("confirm", "cancel"):
        return {"confirm_or_cancel": confirm_or_cancel}
    return


CategoryNameFilter = PatternMatchMessageFilter(
    pattern=r"^[A-Za-zА-Яа-я0-9_,()]{4,30}$",
    return_argname="category_name",
    exception_type=InvalidCategoryName,
)
CategoryTypeFilter = CallbackQueryFilter("category_type", get_category_type)
CategoryIdFIlter = CallbackQueryFilter("category_id", get_category_id)
SelectCategoryPageFilter = CallbackQueryFilter(
    "show_categories_page", get_next_category_page
)
CategoryDeleteConfirmFilter = CallbackQueryFilter(
    "category_delete_cancel", get_confirm_or_cancel
)


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


class EntryCategoryIdFilter(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, int], bool]:
        if callback.data.startswith("entry_category_item"):
            *_, category_id = callback.data.rsplit("_", maxsplit=1)
            return {"category_id": int(category_id)}
        return False


class EntrySumFilter(BaseFilter):
    async def __call__(self, message: Message) -> dict[str, Union[int, str]]:
        transaction_sum, error_message = validate_entry_sum(message.text)
        return {
            "transaction_sum": transaction_sum,
            "error_message": error_message,
        }


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


class BudgetCurrencyFilter(BaseFilter):
    async def __call__(
        self, msg: Message | CallbackQuery
    ) -> dict[str, str | None]:
        user_input = (
            msg.text
            if isinstance(msg, Message)
            else CallbackQuery.message.text
        )

        context = {"filtered_budget_currency": None}

        valid_currency_pattern = r"^[A-Za-zА-Яа-я]{3,10}$"

        if re.match(valid_currency_pattern, user_input):
            context["filtered_budget_currency"] = user_input

        return context
