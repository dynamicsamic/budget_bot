import random

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.db import models
from app.db.models.base import Base
from tests.conf import constants


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def create_tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, create_tables) -> Session:
    connection = engine.connect()
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
def create_budgets(db_session, create_users):
    db_session.add_all(
        [
            models.Budget(
                id=i,
                name=f"budget{i}",
                user_id=i,
            )
            for i in range(1, constants["TEST_SAMPLE_SIZE"] + 1)
        ]
    )
    db_session.commit()


@pytest.fixture
def create_categories(db_session, create_budgets):
    db_session.add_all(
        [
            models.EntryCategory(
                id=i,
                name=f"category{i}",
                type=models.EntryType.EXPENSES
                if i % 2
                else models.EntryType.INCOME,
                budget_id=i,
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
            budget_id=i,
            category_id=i,
        )
        for i in range(1, constants["TEST_SAMPLE_SIZE"] // 2 + 1)
    ]
    negatives = [
        models.Entry(
            id=i,
            sum=random.randint(-1000000, -1),
            description=f"test{i}",
            budget_id=i,
            category_id=i,
        )
        for i in range(
            constants["TEST_SAMPLE_SIZE"] // 2 + 1,
            constants["TEST_SAMPLE_SIZE"] + 1,
        )
    ]
    db_session.add_all(positives + negatives)
    db_session.commit()
