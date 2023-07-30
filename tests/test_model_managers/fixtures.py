import datetime as dt
from typing import Type

import pytest
from sqlalchemy import CheckConstraint, DateTime, Integer, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    scoped_session,
    sessionmaker,
)

from app import settings, utils
from app.db import base, managers, models
from tests.conf import constants

user_data = {
    "test_user": {"id": 999, "tg_username": "test_user", "tg_id": 999}
}


class TestBase(DeclarativeBase):
    pass


class AbstractTestModel(TestBase, base.ModelFieldsDetails):
    __abstract__ = True

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


class BaseTestModel(AbstractTestModel):
    __tablename__ = "testmodel"


class CustomDateTestModel(AbstractTestModel):
    __tablename__ = "custom_date_testmodel"

    custom_datefield: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=dt.datetime.now(settings.TIME_ZONE),
    )


class SumTestModel(AbstractTestModel):
    __tablename__ = "sum_testmodel"

    sum: Mapped[int] = mapped_column(Integer, CheckConstraint("sum != 0"))


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
            BaseTestModel(
                id=i,
                name=f"obj{i}",
                created_at=utils.now(),
                last_updated=utils.now(),
            )
            for i in range(1, constants["TEST_SAMPLE_SIZE"] + 1)
        ]
    )
    db_session.commit()


@pytest.fixture
def base_manager(db_session, populate_db) -> managers.BaseModelManager:
    return managers.BaseModelManager(BaseTestModel, db_session)


@pytest.fixture
def ordered_manager(
    db_session, populate_db
) -> Type[managers.BaseModelManager]:
    return managers.OrderedQueryManager(
        BaseTestModel, db_session, order_by=["created_at", "id"]
    )


@pytest.fixture
def basic_date_manager(
    db_session, populate_db
) -> Type[managers.BaseModelManager]:
    return managers.DateQueryManager(
        BaseTestModel,
        db_session,
        order_by=["created_at", "id"],
    )


@pytest.fixture
def custom_date_manager(db_session) -> Type[managers.BaseModelManager]:
    return managers.DateQueryManager(
        CustomDateTestModel,
        db_session,
        datefield="custom_datefield",
        order_by=["custom_datefield", "created_at", "id"],
    )


@pytest.fixture
def sum_manager(db_session):
    return managers.EntryManager(
        SumTestModel,
        db_session,
        order_by=["created_at", "id"],
    )
