import datetime as dt
from collections import namedtuple
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import CallbackQuery, Message, TelegramObject

from app import settings
from app.bot import keyboards
from app.db import get_session
from app.db.queries.core import BudgetModelController, user_controller
from app.services.user import get_user
from app.utils import DateRange

# TODO: restrict to only private chats in middleware


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


async def redirect_handler(event: TelegramObject, *_, **__):
    message = event.message if isinstance(event, CallbackQuery) else event

    await message.answer(
        "Для работы с ботом, зарегистрируйтесь или активируйте Ваш аккаунт, "
        "выбрав одну из кнопок ниже.",
        reply_markup=keyboards.button_menu(
            keyboards.buttons.signup_user, keyboards.buttons.activate_user
        ),
    )


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


class IdentifyUserMiddleWare(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery | Message,
        data: Dict[str, Any],
    ) -> Any:
        db_session = data.get("db_session")
        if db_session is not None and db_session.is_active:
            user = get_user(db_session, tg_id=event.from_user.id)
            if user is None:
                user = AnonymousUser()
            data["user"] = user
        else:
            with get_session() as db_session:
                user = get_user(db_session, tg_id=event.from_user.id)
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
            return await redirect_handler(event, data)

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
