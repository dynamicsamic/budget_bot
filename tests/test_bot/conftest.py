from datetime import datetime
from functools import partial

import pytest
import pytest_asyncio
from aiogram.enums import ChatType
from aiogram.types import Chat, Message, User

from app.bot import dp
from app.bot.handlers import router

from ..test_utils import MockedBot, Requester

user = User(id=101, is_bot=False, first_name="User", username="username")
chat = Chat(id=1, type=ChatType.PRIVATE)
second_user = User(
    id=102, is_bot=False, first_name="Second", username="second_user"
)
second_chat = Chat(id=2, type=ChatType.PRIVATE)
generic_message = partial(
    Message, message_id=1, date=datetime.now(), from_user=user, chat=chat
)


@pytest.fixture
def mocked_bot():
    return MockedBot()


@pytest.fixture(scope="session")
def dispatcher():
    dp.include_router(router)
    return dp


@pytest_asyncio.fixture
async def requester():
    if router not in set(dp.sub_routers):
        dp.include_router(router)
    r = Requester(dp, MockedBot(), chat, user)
    yield r
    await r.clear_fsm_state()
