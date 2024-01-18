import random
from collections import deque
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Coroutine,
    Deque,
    Dict,
    Optional,
    Tuple,
    Type,
)

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.fsm.context import FSMContext
from aiogram.methods import AnswerCallbackQuery, SendMessage, TelegramMethod
from aiogram.methods.base import Response, TelegramType
from aiogram.types import UNSET_PARSE_MODE, Chat, ResponseParameters, Update
from aiogram.types import User as AiogramUser
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.db.models import Category, CategoryType, Entry, User

USER_SAMPLE = 5
CATEGORY_SAMPLE = 15
TG_ID_PREFIX = 100
TARGET_USER_ID = 1
TARGET_CATEGORY_ID = 1
EXPENSES_SAMPLE = 10
INCOME_SAMPLE = 5
POSITIVE_ENTRIES_SAMPLE = 25
NEGATIVE_ENTRIES_SAMPLE = 35


class MockModel:
    def __init__(self, **kwargs) -> None:
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __call__(self) -> dict[str, Any]:
        return self.__dict__

    def keys(self):
        return self.__dict__.keys()

    def __getitem__(self, key):
        return getattr(self, key, None)


def create_test_db_session(
    engine: Engine,
) -> Tuple[Connection, scoped_session]:
    connection = engine.connect()
    connection.execution_options(stream_results=True, max_row_buffer=1)
    connection.begin()
    return (
        connection,
        scoped_session(sessionmaker(bind=connection, autoflush=False)),
    )


def create_test_users(db_session):
    db_session.add_all(
        [User(id=i, tg_id=TG_ID_PREFIX + i) for i in range(1, USER_SAMPLE + 1)]
    )
    db_session.commit()


def create_test_categories(db_session):
    expenses = [
        Category(
            id=i,
            name=f"category{i}",
            type=CategoryType.EXPENSES,
            user_id=TARGET_USER_ID,
        )
        for i in range(1, EXPENSES_SAMPLE + 1)
    ]
    income = [
        Category(
            id=i,
            name=f"category{i}",
            type=CategoryType.INCOME,
            user_id=TARGET_USER_ID,
        )
        for i in range(
            EXPENSES_SAMPLE + 1,
            INCOME_SAMPLE + EXPENSES_SAMPLE + 1,
        )
    ]
    db_session.add_all(expenses + income)
    db_session.commit()


def create_test_entries(db_session):
    positives = [
        Entry(
            id=i,
            sum=random.randint(1, 1000000),
            description=f"test{i}",
            user_id=TARGET_USER_ID,
            category_id=TARGET_CATEGORY_ID,
        )
        for i in range(1, POSITIVE_ENTRIES_SAMPLE + 1)
    ]
    negatives = [
        Entry(
            id=i,
            sum=random.randint(-1000000, -1),
            description=f"test{i}",
            user_id=TARGET_USER_ID,
            category_id=TARGET_CATEGORY_ID,
        )
        for i in range(
            POSITIVE_ENTRIES_SAMPLE + 1,
            NEGATIVE_ENTRIES_SAMPLE + POSITIVE_ENTRIES_SAMPLE + 1,
        )
    ]
    db_session.add_all(positives + negatives)
    db_session.commit()


def get_dispatcher_context(
    dispatcher: Dispatcher,
    bot: Bot,
    chat: Chat,
    user: AiogramUser,
) -> FSMContext:
    return dispatcher.fsm.get_context(bot, chat.id, user.id)


async def get_dispatcher_state(
    dispatcher: Dispatcher,
    bot: Bot,
    chat: Chat,
    user: AiogramUser,
) -> Coroutine[Any, Any, str | None]:
    return await get_dispatcher_context(
        dispatcher, bot, chat, user
    ).get_state()


async def get_dispatcher_state_data(
    dispatcher: Dispatcher,
    bot: Bot,
    chat: Chat,
    user: AiogramUser,
) -> Coroutine[Any, Any, Dict[str, Any]]:
    return await get_dispatcher_context(dispatcher, bot, chat, user).get_data()


async def clear_dispatcher_state(
    dispatcher: Dispatcher,
    bot: Bot,
    chat: Chat,
    user: AiogramUser,
) -> Coroutine[Any, Any, None]:
    return await get_dispatcher_context(dispatcher, bot, chat, user).clear()


@dataclass
class Requester:
    dispather: Dispatcher
    mocked_bot: "MockedBot"
    target_chat: Chat
    target_user: AiogramUser

    @property
    def requests(self):
        return self.mocked_bot.session.requests

    async def make_request(
        self, aiogram_method: Type[TelegramMethod], update: Update
    ):
        if aiogram_method is AnswerCallbackQuery:
            # also need to add result for sending inline keyboard
            self.mocked_bot.add_result_for(method=SendMessage, ok=True)

        self.mocked_bot.add_result_for(method=aiogram_method, ok=True)
        await self.dispather.feed_update(self.mocked_bot, update)

    def _get_fsm_context(self) -> FSMContext:
        return self.dispather.fsm.get_context(
            self.mocked_bot, self.target_chat.id, self.target_user.id
        )

    async def get_fsm_state(self):
        return await self._get_fsm_context().get_state()

    async def set_fsm_state(self, state):
        return await self._get_fsm_context().set_state(state)

    async def get_fsm_state_data(self):
        return await self._get_fsm_context().get_data()

    async def update_fsm_state_data(self, **kwargs):
        return await self._get_fsm_context().update_data(**kwargs)

    async def clear_fsm_state(self):
        return await self._get_fsm_context().clear()

    def read_last_sent_message(self):
        requests = self.requests
        if len(requests) == 0:
            return None

        for i in range(-1, -len(requests) - 1, -1):
            if isinstance(message := requests[i], SendMessage):
                return message

    def read_last_request(self) -> TelegramMethod[TelegramType] | None:
        requests = self.requests
        if len(requests) == 0:
            return None
        return requests[-1]


# The following code mostly copied directly from
# https://github.com/aiogram/aiogram/tests/mocked_bot.py
# and serves for testing purpose only.
# All rights for the following code belong to Aiogram.


class MockedSession(BaseSession):
    def __init__(self):
        super(MockedSession, self).__init__()
        self.responses: Deque[Response[TelegramType]] = deque()
        self.requests: Deque[TelegramMethod[TelegramType]] = deque()
        self.closed = True

    def add_result(
        self, response: Response[TelegramType]
    ) -> Response[TelegramType]:
        self.responses.append(response)
        return response

    def get_request(self) -> TelegramMethod[TelegramType]:
        return self.requests.pop()

    async def close(self):
        self.closed = True

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: Optional[int] = UNSET_PARSE_MODE,
    ) -> TelegramType:
        self.closed = False
        self.requests.append(method)
        response: Response[TelegramType] = self.responses.pop()
        self.check_response(
            bot=bot,
            method=method,
            status_code=response.error_code,
            content=response.model_dump_json(),
        )
        return response.result  # type: ignore

    async def stream_content(
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        yield b""


class MockedBot(Bot):
    if TYPE_CHECKING:
        session: MockedSession

    def __init__(self, **kwargs):
        super(MockedBot, self).__init__(
            kwargs.pop("token", "42:TEST"), session=MockedSession(), **kwargs
        )
        self._me = AiogramUser(
            id=self.id,
            is_bot=True,
            first_name="FirstName",
            last_name="LastName",
            username="tbot",
            language_code="ru-RU",
        )

    def add_result_for(
        self,
        method: Type[TelegramMethod[TelegramType]],
        ok: bool,
        result: TelegramType = None,
        description: Optional[str] = None,
        error_code: int = 200,
        migrate_to_chat_id: Optional[int] = None,
        retry_after: Optional[int] = None,
    ) -> Response[TelegramType]:
        response = Response[method.__returning__](  # type: ignore
            ok=ok,
            result=result,
            description=description,
            error_code=error_code,
            parameters=ResponseParameters(
                migrate_to_chat_id=migrate_to_chat_id,
                retry_after=retry_after,
            ),
        )
        self.session.add_result(response)
        return response

    def get_request(self) -> TelegramMethod[TelegramType]:
        return self.session.get_request()
