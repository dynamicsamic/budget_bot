import random

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.db import base, managers, models
from tests.conf import constants

user_data = {
    "test_user": {"id": 999, "tg_username": "test_user", "tg_id": 999}
}


@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite://", echo=True)


@pytest.fixture(scope="session")
def create_tables(engine):
    base.Base.metadata.create_all(bind=engine)
    yield
    base.Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, create_tables):
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
            models.User(id=i, tg_id=f"100{i}", tg_username=f"user{i}")
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
    salary = models.EntryCategory(
        id=1, name="salary", type=models.EntryType.INCOME, user_id=1
    )
    investment = models.EntryCategory(
        id=2, name="investment", type=models.EntryType.INCOME, user_id=1
    )
    products = models.EntryCategory(
        id=3, name="products", type=models.EntryType.EXPENSES, user_id=1
    )
    sports = models.EntryCategory(
        id=4, name="sports", type=models.EntryType.EXPENSES, user_id=1
    )
    pets = models.EntryCategory(
        id=5, name="pets", type=models.EntryType.EXPENSES, user_id=1
    )

    db_session.add_all([salary, investment, products, sports, pets])
    db_session.commit()


expenses = [
    {"id": 1, "budget_id": 1, "category_id": 3, "sum": -200},
    {"id": 2, "budget_id": 1, "category_id": 3, "sum": -1},
    {"id": 3, "budget_id": 1, "category_id": 3, "sum": -10000},
    {"id": 4, "budget_id": 1, "category_id": 4, "sum": -1000},
    {"id": 5, "budget_id": 1, "category_id": 4, "sum": -100000},
    {"id": 6, "budget_id": 1, "category_id": 5, "sum": -999999},
    {"id": 12, "budget_id": 2, "category_id": 5, "sum": -999999},
]
income = [
    {"id": 7, "budget_id": 1, "category_id": 1, "sum": 200},
    {"id": 8, "budget_id": 1, "category_id": 1, "sum": 1},
    {"id": 9, "budget_id": 1, "category_id": 1, "sum": 10000234},
    {"id": 10, "budget_id": 1, "category_id": 2, "sum": 1000},
    {"id": 11, "budget_id": 1, "category_id": 2, "sum": 993939919},
    {"id": 13, "budget_id": 2, "category_id": 1, "sum": 9939},
    {"id": 14, "budget_id": 2, "category_id": 2, "sum": 993939919},
]


@pytest.fixture
def create_entries(db_session, create_categories):
    db_session.add_all(
        [
            *[models.Entry(**d) for d in expenses],
            *[models.Entry(**d) for d in income],
        ]
    )
    db_session.commit()


@pytest.fixture
def user_manager(db_session, create_users):
    return managers.DateQueryManager(models.User, session=db_session)


@pytest.fixture
def entry_manager(db_session, create_entries):
    return managers.EntryManager(
        models.Entry,
        db_session,
        order_by=["transaction_date", "id"],
        datefield="transaction_date",
    )
