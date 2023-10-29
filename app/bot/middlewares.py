import datetime as dt
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import CallbackQuery, Message, TelegramObject

from app import settings
from app.db import get_session, managers
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


class CurrentUserMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        with get_session() as db_session:
            data["user"] = managers.UserManager(session=db_session).get_by(
                tg_id=event.from_user.id
            )
        return await handler(event, data)


class ModelManagerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        model_managers: list[managers.BaseModelManager] = get_flag(
            data, "model_managers"
        )

        if not model_managers:
            return await handler(event, data)

        with get_session() as db_session:
            for manager in model_managers:
                manager_name = f"{manager.model.__tablename__}_manager"
                data[manager_name] = manager(db_session)

            return await handler(event, data)
