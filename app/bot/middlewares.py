from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app import settings
from app.utils import DateGen


class DateInfoMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        datetime = (
            event.message.date
            if isinstance(event, CallbackQuery)
            else event.date
        )
        data["date_info"] = DateGen(datetime.astimezone(settings.TIME_ZONE))
        return await handler(event, data)
