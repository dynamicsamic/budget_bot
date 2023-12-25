import random
from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.db import models
from app.db.models import Base
from app.db.repository import (
    CategoryRepository,
    EntryRepository,
    UserRepository,
)
from tests.conf import constants


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
            models.User(id=i, tg_id=f"100{i}")
            for i in range(1, constants["TEST_SAMPLE_SIZE"] + 1)
        ]
    )
    db_session.commit()


@pytest.fixture
def create_categories(db_session, create_users):
    db_session.add_all(
        [
            models.Category(
                id=i,
                name=f"category{i}",
                type=models.CategoryType.EXPENSES
                if i % 2
                else models.CategoryType.INCOME,
                user_id=i,
            )
            for i in range(1, constants["TEST_SAMPLE_SIZE"] + 1)
        ]
    )
    db_session.commit()


@pytest.fixture
def create_entries(db_session, create_categories):
    positives = [
        models.Entry(
            id=i,
            sum=random.randint(1, 1000000),
            description=f"test{i}",
            user_id=i,
            category_id=i,
        )
        for i in range(1, constants["TEST_SAMPLE_SIZE"] // 2 + 1)
    ]
    negatives = [
        models.Entry(
            id=i,
            sum=random.randint(-1000000, -1),
            description=f"test{i}",
            user_id=i,
            category_id=i,
        )
        for i in range(
            constants["TEST_SAMPLE_SIZE"] // 2 + 1,
            constants["TEST_SAMPLE_SIZE"] + 1,
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
