import datetime as dt

import pytest
from sqlalchemy import DateTime
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    scoped_session,
    sessionmaker,
)

from app import settings, utils
from app.db.models import base
from tests.conf import constants


class TestBase(DeclarativeBase):
    pass


class BaseTestModel(TestBase, base.ModelFieldsDetails):
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

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, Name={self.name}, "
            f"Created_at={self.created_at}, "
            f"Custom_datefield={self.custom_datefield})"
        )


@pytest.fixture(scope="session")
def create_test_tables(inmemory_engine):
    TestBase.metadata.create_all(bind=inmemory_engine)
    yield
    TestBase.metadata.drop_all(bind=inmemory_engine)


@pytest.fixture
def db_session(inmemory_engine, create_test_tables) -> Session:
    connection = inmemory_engine.connect()
    connection.begin()
    session = scoped_session(sessionmaker(bind=connection, autoflush=False))

    yield session

    session.close()
    connection.close()


@pytest.fixture
def populate_generic_table(db_session: Session):
    db_session.add_all(
        [
            BaseTestModel(
                id=i,
                name=f"obj{i}",
                created_at=utils.now(),
                custom_datefield=utils.now(),
            )
            for i in range(1, constants["TEST_SAMPLE_SIZE"] + 1)
        ]
    )
    db_session.commit()
