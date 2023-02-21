import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import models

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
Session = sessionmaker(bind=engine)


@pytest.fixture(scope="module")
def db_session():
    models.Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="module")
def test_user():
    test_user = models.User(tg_username="dynamicsamic", tg_id=1)
    return test_user


def test_author(db_session, test_user):
    db_session.add(test_user)
    db_session.commit()
    user = (
        db_session.query(models.User).filter_by(models.User.tg_id == 1).first()
    )
    assert user.tg_id == 1
