import random
from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.db.models import Base, Category, CategoryType, Entry, User
from app.db.repository import (
    CategoryRepository,
    EntryRepository,
    UserRepository,
)

TG_ID_PREFIX = 100
START_INDEX = 1
USER_SAMPLE = 5
EXPENSES_SAMPLE = 30
INCOME_SAMPLE = 15
POSITIVE_ENTRIES_SAMPLE = 50
NEGATIVE_ENTRIES_SAMPLE = 80


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


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def create_tables(inmemory_engine):
    Base.metadata.create_all(bind=inmemory_engine)
    yield
    Base.metadata.drop_all(bind=inmemory_engine)


@pytest.fixture
def db_session(inmemory_engine, create_tables) -> Session:
    connection = inmemory_engine.connect()
    connection.execution_options(stream_results=True, max_row_buffer=1)
    connection.begin()
    session = scoped_session(sessionmaker(bind=connection, autoflush=False))

    yield session

    session.close()
    # transaction.rollback()
    connection.close()


@pytest.fixture
def create_users(db_session):
    db_session.add_all(
        [
            User(id=i, tg_id=100 + i)
            for i in range(START_INDEX, USER_SAMPLE + START_INDEX)
        ]
    )
    db_session.commit()


@pytest.fixture
def create_categories(db_session, create_users):
    expenses = [
        Category(
            id=i,
            name=f"category{i}",
            type=CategoryType.EXPENSES,
            user_id=i % USER_SAMPLE + 1 or START_INDEX,
        )
        for i in range(START_INDEX, EXPENSES_SAMPLE + START_INDEX)
    ]
    income = [
        Category(
            id=i,
            name=f"category{i}",
            type=CategoryType.INCOME,
            user_id=i % USER_SAMPLE + 1 or START_INDEX,
        )
        for i in range(
            EXPENSES_SAMPLE + START_INDEX,
            INCOME_SAMPLE + EXPENSES_SAMPLE + START_INDEX,
        )
    ]
    db_session.add_all(expenses + income)
    db_session.commit()


@pytest.fixture
def create_entries(db_session, create_categories):
    positives = [
        Entry(
            id=i,
            sum=random.randint(1, 1000000),
            description=f"test{i}",
            user_id=i % USER_SAMPLE + 1 or START_INDEX,
            category_id=i % INCOME_SAMPLE + 1 or 1,
        )
        for i in range(START_INDEX, POSITIVE_ENTRIES_SAMPLE + START_INDEX)
    ]
    negatives = [
        Entry(
            id=i,
            sum=random.randint(-1000000, -1),
            description=f"test{i}",
            user_id=i % USER_SAMPLE + 1 or START_INDEX,
            category_id=i % EXPENSES_SAMPLE + 1 or 1,
        )
        for i in range(
            POSITIVE_ENTRIES_SAMPLE + START_INDEX,
            NEGATIVE_ENTRIES_SAMPLE + POSITIVE_ENTRIES_SAMPLE + START_INDEX,
        )
    ]
    db_session.add_all(positives + negatives)
    db_session.commit()


@pytest.fixture
def catrep(db_session):
    yield CategoryRepository(db_session)


@pytest.fixture
def usrrep(db_session):
    yield UserRepository(db_session)


@pytest.fixture
def entrep(db_session):
    yield EntryRepository(db_session)
