import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session as sqlalchemy_session
from sqlalchemy.orm import sessionmaker

from app.db import models

from . import factories
from .conf import constants

engine = create_engine(
    "sqlite+pysqlite:///:memory:", echo=True, query_cache_size=0
)
Session = sessionmaker(bind=engine)

user_data = {
    "test_user": {"id": 999, "tg_username": "test_user", "tg_id": 999}
}


@pytest.fixture(scope="module")
def db_session() -> sqlalchemy_session:
    models.Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="module")
def users(db_session: sqlalchemy_session):
    factories.UserFactory._meta.sqlalchemy_session = db_session
    factories.UserFactory.reset_sequence(constants["START_SEQUNCE_FROM"])
    factories.UserFactory.create_batch(constants["USER_NUM"])


@pytest.fixture(scope="module")
def test_user():
    test_user = models.User(**user_data["test_user"])
    return test_user
