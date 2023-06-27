import datetime as dt
from functools import cache
from typing import Any, Self, Type

import pytest
from sqlalchemy import DateTime, String, create_engine, func, select, text
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    scoped_session,
    sessionmaker,
)

from app import settings
from app.db import base, models, test_engine
from app.db.managers import BaseModelManager, DateQueryManager
from tests.conf import constants

user_data = {
    "test_user": {"id": 999, "tg_username": "test_user", "tg_id": 999}
}


class TestBase(DeclarativeBase):
    pass


class MyTestModel(TestBase, base.ModelFieldsDetails):
    __tablename__ = "testmodel"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.now(settings.TIME_ZONE)
    )
    last_updated: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=dt.datetime.now(settings.TIME_ZONE),
        onupdate=dt.datetime.now(settings.TIME_ZONE),
    )


@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite://", echo=True)


@pytest.fixture(scope="session")
def create_tables(engine):
    TestBase.metadata.create_all(bind=engine)
    yield
    TestBase.metadata.drop_all(bind=engine)


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
def populate_db(db_session: Session):
    db_session.add_all(
        [
            MyTestModel(id=i, name=f"obj{i}")
            for i in range(1, constants["TEST_SAMPLE_SIZE"] + 1)
        ]
    )
    db_session.commit()


@pytest.fixture
def base_manager(db_session, populate_db) -> BaseModelManager:
    return BaseModelManager(MyTestModel, db_session)


@pytest.fixture
def date_manager(db_session, populate_db) -> Type[BaseModelManager]:
    return DateQueryManager(MyTestModel, db_session)
