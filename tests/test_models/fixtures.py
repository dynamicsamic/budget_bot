import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.db import base, models
from app.db.managers import BaseModelManager
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
            models.User(tg_id=f"100{i}", tg_username=f"user{i}")
            for i in range(1, constants["TEST_SAMPLE_SIZE"] + 1)
        ]
    )
    db_session.commit()


@pytest.fixture
def user_manager(db_session, create_users):
    return BaseModelManager(models.User, db_session)
