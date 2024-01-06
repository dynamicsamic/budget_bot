import pytest

from app.bot import dp
from app.bot.handlers import router

from ..test_utils import MockedBot


@pytest.fixture
def mocked_bot():
    return MockedBot()


@pytest.fixture(scope="session")
def dispatcher():
    dp.include_router(router)
    return dp
