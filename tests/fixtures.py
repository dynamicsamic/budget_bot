import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import models

engine = create_engine(
    "sqlite+pysqlite:///:memory:", echo=True, query_cache_size=0
)
Session = sessionmaker(bind=engine)

user_data = {"test_user": {"tg_username": "dynamicsamic", "tg_id": 10}}


@pytest.fixture(scope="module")
def db_session():
    models.Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="module")
def test_user():
    test_user = models.User(**user_data["test_user"])
    return test_user
