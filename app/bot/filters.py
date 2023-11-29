import re
from datetime import datetime
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app import settings
from app.utils import (
    validate_category_name,
    validate_entry_date,
    validate_entry_sum,
)


class BudgetNameFilter(BaseFilter):
    async def __call__(self, msg: Message) -> dict[str, str | None]:
        valid_name_pattern = r"^[A-Za-zА-Яа-я0-9-_]{4,25}$"
        context = {"filtered_budget_name": None}

        if re.match(valid_name_pattern, msg.text):
            context["filtered_budget_name"] = msg.text

        return context


class BudgetCurrencyFilter(BaseFilter):
    async def __call__(self, msg: Message) -> dict[str, str | None]:
        valid_currency_pattern = r"^[A-Za-zА-Яа-я]{3,10}$"
        context = {"filtered_budget_currency": None}

        if re.match(valid_currency_pattern, msg.text):
            context["filtered_budget_currency"] = msg.text

        return context


class CategoryNameFilter(BaseFilter):
    async def __call__(self, message: Message):
        category_name, error_message = validate_category_name(message.text)
        return {"category_name": category_name, "error_message": error_message}


class CategoryTypeFilter(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, str], bool]:
        if callback.data.startswith("choose_entry_category"):
            *_, category_type = callback.data.rsplit("_", maxsplit=1)
            return {"category_type": category_type}
        return False


class GetEntryId(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, int], bool]:
        if callback.data.startswith("entry_id"):
            *_, entry_id = callback.data.rsplit("_", maxsplit=1)
            return {"entry_id": entry_id}
        return False


class EntryBudgetIdFilter(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, int], bool]:
        if callback.data.startswith("entry_budget_item"):
            *_, budget_id = callback.data.rsplit("_", maxsplit=1)
            return {"budget_id": budget_id}
        return False


class EntryCategoryIdFilter(BaseFilter):
    async def __call__(
        self, callback: CallbackQuery
    ) -> Union[dict[str, int], bool]:
        if callback.data.startswith("entry_category_item"):
            *_, category_id = callback.data.rsplit("_", maxsplit=1)
            return {"category_id": category_id}
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
