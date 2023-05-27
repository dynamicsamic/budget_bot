import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.db import models

from .conf import constants

user_data = {
    "test_user": {"id": 999, "tg_username": "test_user", "tg_id": 999}
}


@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite://", echo=True)


@pytest.fixture(scope="session")
def create_tables(engine):
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


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
def users(db_session: Session):
    db_session.add_all(
        [
            models.User(id=i, tg_id=1000 + i, tg_username=f"tg_user{i}")
            for i in range(1, constants["USER_NUM"] + 1)
        ]
    )
    db_session.commit()
