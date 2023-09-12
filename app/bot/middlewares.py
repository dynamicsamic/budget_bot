import datetime as dt
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app import settings
from app.db import get_session, managers, models
from app.utils import DateGen

# TODO: restrict to only private chats in middleware


class DateInfoMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            datetime = event.date
        elif isinstance(event, CallbackQuery):
            datetime = event.message.date
        else:
            datetime = dt.datetime.now()
        data["date_info"] = DateGen(datetime.astimezone(settings.TIME_ZONE))
        return await handler(event, data)


class DataBaseSessionMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        with get_session() as db_session:
            data["user"] = (
                db_session.query(models.User)
                .filter_by(tg_id=event.from_user.id)
                .one_or_none()
            )
            model_managers = {
                "user": managers.user_manager(db_session),
                "budget": managers.budget_manager(db_session),
                "category": managers.category_manager(db_session),
            }
            data["model_managers"] = model_managers
            return await handler(event, data)
