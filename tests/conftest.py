import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session

from app.db import db_session, inmemory_test_engine, test_engine
from app.db.models import Base

from .test_utils import (
    create_test_categories,
    create_test_db_session,
    create_test_entries,
    create_test_users,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


##################
#    FIXSTURES   #
#       FOR      #
# NON-PERSISTENT #
#    DATABASE    #
##################


@pytest.fixture(scope="session")
def inmemory_engine():
    return inmemory_test_engine


@pytest.fixture(scope="session")
def create_inmemory_tables(inmemory_engine):
    Base.metadata.create_all(bind=inmemory_engine)
    yield
    Base.metadata.drop_all(bind=inmemory_engine)


@pytest.fixture
def inmemory_db_session(
    inmemory_engine, create_inmemory_tables
) -> scoped_session:
    connection, session = create_test_db_session(inmemory_engine)

    yield session

    session.close()
    connection.close()


@pytest.fixture
def create_inmemory_users(inmemory_db_session):
    create_test_users(inmemory_db_session)


@pytest.fixture
def create_inmemory_categories(inmemory_db_session, create_inmemory_users):
    create_test_categories(inmemory_db_session)


@pytest.fixture
def create_inmemory_entries(inmemory_db_session, create_inmemory_categories):
    create_test_entries(inmemory_db_session)


##################
#    FIXSTURES   #
#       FOR      #
#   PERSISTENT   #
#    DATABASE    #
##################


@pytest.fixture
def persistent_db_session():
    with db_session() as session:
        yield session


@pytest.fixture
def create_test_tables():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def create_test_data():
    Base.metadata.create_all(bind=test_engine)
    with db_session() as session:
        create_test_users(session)
        create_test_categories(session)
        create_test_entries(session)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def persistent_test_engine():
    return test_engine


@pytest.fixture(scope="module")
def create_persistent_tables(persistent_test_engine):
    Base.metadata.create_all(bind=persistent_test_engine)
    yield
    Base.metadata.drop_all(bind=persistent_test_engine)
