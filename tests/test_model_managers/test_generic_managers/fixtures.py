import datetime as dt

import pytest
from sqlalchemy import DateTime, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    scoped_session,
    sessionmaker,
)

from app import settings, utils
from app.db import base, managers
from tests.conf import constants


class TestBase(DeclarativeBase):
    pass


class GenericTestModel(TestBase, base.ModelFieldsDetails):
    __tablename__ = "testmodel"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.now(settings.TIME_ZONE)
    )
    custom_datefield: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=dt.datetime.now(settings.TIME_ZONE),
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
def populate_tables(db_session: Session):
    db_session.add_all(
        [
            GenericTestModel(
                id=i,
                name=f"obj{i}",
                created_at=utils.now(),
                custom_datefield=utils.now(),
            )
            for i in range(1, constants["TEST_SAMPLE_SIZE"] + 1)
        ]
    )
    db_session.commit()


@pytest.fixture
def generic_manager(db_session, populate_tables):
    return managers.ModelManager(GenericTestModel, db_session)


@pytest.fixture
def default_datefield_manager(db_session, populate_tables):
    return managers.DateQueryManager(GenericTestModel, db_session)


@pytest.fixture
def custom_datefield_manager(db_session, populate_tables):
    return managers.DateQueryManager(
        GenericTestModel, db_session, datefield="custom_datefield"
    )
