import datetime as dt
import logging
from collections import namedtuple
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import CallbackQuery, Message, TelegramObject

from app import settings
from app.bot.replies.keyboards.user import (
    user_activation_menu,
    user_signup_menu,
)
from app.db import db_session
from app.db.repository import (
    CategoryRepository,
    EntryRepository,
    UserRepository,
    get_user,
)
from app.utils import DateRange, aiogram_log_handler

# TODO: restrict to only private chats in middleware

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)


def AnonymousUser():
    anonymous = namedtuple(
        "AnonymousUser",
        [
            "id",
            "tg_id",
            "is_active",
            "is_anonymous",
            "created_at",
            "updated_at",
        ],
    )
    return anonymous(-1, -1, False, True, -1, -1)


async def redirect_inactive_user(event: TelegramObject, *_, **__):
    message = event if isinstance(event, Message) else event.message

    await message.answer(
        "Для работы с ботом, активируйте Ваш аккаунт, нажав на кнопку ниже.",
        reply_markup=user_activation_menu,
    )
    logger.info("SUCCESS: anonymous user redirected")


async def redirect_anonymous_user(event: TelegramObject, *_, **__):
    message = event if isinstance(event, Message) else event.message

    await message.answer(
        "Для работы с ботом, зарегистрируйтесь, нажав на кнопку ниже.",
        reply_markup=user_signup_menu,
    )
    logger.info("SUCCESS: anonymous user redirected")


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
        with db_session() as session:
            data["db_session"] = session
        return await handler(event, data)


class IdentifyUserMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        session = data.get("db_session")
        if session is not None and session.is_active:
            user = get_user(session, tg_id=event.from_user.id)
            if user is None:
                user = AnonymousUser()
            data["user"] = user

        else:
            with db_session() as session:
                user = get_user(session, tg_id=event.from_user.id)
                if user is None:
                    user = AnonymousUser()
                data["user"] = user

        return await handler(event, data)


class RedirectAnonymousUserMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        allow_anonymous = get_flag(data, "allow_anonymous", default=False)
        user = data.get("user")

        if not user.is_active and not allow_anonymous:
            if user.is_anonymous:
                return await redirect_anonymous_user(event, data)
            return await redirect_inactive_user(event, data)

        return await handler(event, data)


class UserRepositoryMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        session = data.get("db_session")
        if session is not None and session.is_active:
            data["repository"] = UserRepository(session)
        else:
            with db_session() as session:
                data["repository"] = UserRepository(session)
        return await handler(event, data)


class CategoryRepositoryMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        session = data.get("db_session")
        if session is not None and session.is_active:
            data["repository"] = CategoryRepository(session)
        else:
            with db_session() as session:
                data["repository"] = CategoryRepository(session)
        return await handler(event, data)


class EntryRepositoryMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        session = data.get("db_session")
        if session is not None and session.is_active:
            data["ca_repository"] = CategoryRepository(session)
            data["en_repository"] = EntryRepository(session)
        else:
            with db_session() as session:
                data["ca_repository"] = CategoryRepository(session)
                data["en_repository"] = EntryRepository(session)
        return await handler(event, data)
