import re
from datetime import datetime
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app import settings
from app.db.models import CategoryType
from app.utils import validate_entry_date, validate_entry_sum

from . import prompts


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


class ExtractBudgetIdFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> dict[str, int | None]:
        if callback.data.startswith("budget_item"):
            extracted_budget_id = callback.data.rsplit("_", maxsplit=1)[-1]

            if extracted_budget_id.isdigit():
                return {"extracted_budget_id": int(extracted_budget_id)}

            return {"extracted_budget_id": None}


class CategoryNameFilter(BaseFilter):
    async def __call__(self, message: Message) -> dict[str, str | None]:
        valid_name_pattern = r"^[A-Za-zА-Яа-я0-9_,()]{4,30}$"
        user_input = message.text

        context = {
            "filtered_category_name": None,
            "error_message": (
                "Недопустимое название категории."
                f"{prompts.category_name_description}"
            ),
        }

        if re.match(valid_name_pattern, user_input):
            context["filtered_category_name"] = user_input.lower()
            context["error_message"] = None

        return context


class CategoryTypeFilter(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, CategoryType], bool]:
        if callback.data.startswith("select_category_type"):
            category_type = get_suffix(callback.data)
            if category_type == "income":
                return {"category_type": CategoryType.INCOME}

            return {"category_type": CategoryType.EXPENSES}

        return False


class SelectPaginatorPageFilter(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, CategoryType], bool]:
        if callback.data.startswith("category_page_num"):
            if switch_to := get_suffix(callback.data):
                return {"switch_to_page": switch_to}

        return False


class CategoryIdFIlter(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, int], bool]:
        if callback.data.startswith("category_id"):
            category_id = get_suffix(callback.data)
            return {"category_id": int(category_id)}
        return False


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
