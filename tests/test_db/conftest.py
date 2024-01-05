import pytest

from app.db.repository import (
    CategoryRepository,
    EntryRepository,
    UserRepository,
)


@pytest.fixture
def usrrep(inmemory_db_session):
    return UserRepository(inmemory_db_session)


@pytest.fixture
def catrep(inmemory_db_session):
    return CategoryRepository(inmemory_db_session)


@pytest.fixture
def entrep(inmemory_db_session):
    return EntryRepository(inmemory_db_session)
