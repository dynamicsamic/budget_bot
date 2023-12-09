import datetime as dt
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app import settings
from app.db import get_session
from app.db.queries.core import BudgetModelController, user_controller
from app.services.user import get_user
from app.utils import DateRange

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
        data["date_info"] = DateRange(datetime.astimezone(settings.TIME_ZONE))
        return await handler(event, data)


class DbSessionMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        with get_session() as db_session:
            data["db_session"] = db_session
        return await handler(event, data)


class CurrentUserMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        db_session = data.get("db_session")
        if db_session is not None and db_session.is_active:
            data["user"] = get_user(db_session, tg_id=event.from_user.id)
        else:
            with get_session() as db_session:
                data["user"] = get_user(db_session, tg_id=event.from_user.id)
        return await handler(event, data)


class AddUserControllerMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        db_session = data.get("db_session")
        if db_session is not None and db_session.is_active:
            data["user_controller"] = user_controller(db_session)
        else:
            with get_session() as db_session:
                data["user_controller"] = user_controller(db_session)
        return await handler(event, data)


class AddBudgetControllerMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        db_session = data.get("db_session")
        if db_session is not None and db_session.is_active:
            data["budget_controller"] = BudgetModelController(db_session)
        else:
            with get_session() as db_session:
                data["budget_controller"] = BudgetModelController(db_session)
        return await handler(event, data)
