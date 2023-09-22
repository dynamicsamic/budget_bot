from datetime import datetime
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app import settings
from app.utils import validate_entry_date, validate_entry_sum


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
