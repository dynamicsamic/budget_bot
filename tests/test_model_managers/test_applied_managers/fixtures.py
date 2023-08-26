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
        name="salary", type=models.EntryType.INCOME, user_id=1
    )
    investment = models.EntryCategory(
        name="investment", type=models.EntryType.INCOME, user_id=1
    )
    products = models.EntryCategory(
        name="products", type=models.EntryType.EXPENSES, user_id=1
    )
    sports = models.EntryCategory(
        name="sports", type=models.EntryType.EXPENSES, user_id=1
    )
    pets = models.EntryCategory(
        name="pets", type=models.EntryType.EXPENSES, user_id=1
    )

    db_session.add_all([salary, investment, products, sports, pets])
    db_session.commit()


@pytest.fixture
def create_entries(db_session, create_categories):
    expenses = [
        models.Entry(budget_id=1, category_id=3, sum=-200),
        models.Entry(budget_id=1, category_id=3, sum=-1),
        models.Entry(budget_id=1, category_id=3, sum=-10000),
        models.Entry(budget_id=1, category_id=4, sum=-1000),
        models.Entry(budget_id=1, category_id=4, sum=-100000),
        models.Entry(budget_id=1, category_id=5, sum=-999999),
    ]
    income = [
        models.Entry(budget_id=1, category_id=1, sum=200),
        models.Entry(budget_id=1, category_id=1, sum=1),
        models.Entry(budget_id=1, category_id=1, sum=10000),
        models.Entry(budget_id=1, category_id=2, sum=1000),
        models.Entry(budget_id=1, category_id=2, sum=100000),
    ]
    db_session.add_all([*expenses, *income])
    db_session.commit()


@pytest.fixture
def user_manager(db_session, create_users):
    return managers.DateQueryManager(models.User, session=db_session)
