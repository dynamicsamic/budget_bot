import datetime as dt
from functools import cache

import pytest
from sqlalchemy import DateTime, String, create_engine, select, text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    scoped_session,
    sessionmaker,
)

from app import settings
from app.db import models, test_engine

from .conf import constants


class MockBase(DeclarativeBase):
    pass


class MockModel(MockBase):
    __tablename__ = "mockmodel"

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

    @classmethod
    @property
    @cache
    def queries(cls):
        return models.QueryManager(cls)


@pytest.fixture(scope="session")
def create_tables():
    MockBase.metadata.create_all(bind=test_engine)
    yield
    MockBase.metadata.drop_all(bind=test_engine)


# @pytest.fixture
# def db_session(create_tables) -> Session:
#     session_factory = sessionmaker(test_engine)
#     session = session_factory()

#     yield session

#     session.close()


@pytest.fixture(scope="module")
def db_session():
    """Create db tables and share session across all tests in module."""
    MockBase.metadata.create_all(bind=test_engine)
    session = Session(bind=test_engine)
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def populate_db(db_session: Session):
    db_session.query(MockModel).delete()
    db_session.add_all(
        [
            MockModel(id=i, name=f"obj{i}")
            for i in range(1, constants["TEST_SAMPLE_SIZE"] + 1)
        ]
    )
    try:
        db_session.commit()
    except Exception:
        db_session.rollback()
    finally:
        db_session.close()


def test_setup(db_session, populate_db):
    pass


def test_count_method_bound_session_return_number_of_all_instances(db_session):
    num_entries = MockModel.queries.count(db_session)
    assert num_entries == constants["TEST_SAMPLE_SIZE"]
    assert isinstance(num_entries, int)


def test_count_method_sessionless_return_number_of_all_instances():
    num_entries = MockModel.queries.count()
    assert num_entries == constants["TEST_SAMPLE_SIZE"]
    assert isinstance(num_entries, int)


def test_all_method_bound_session_without_args_return_scalar_result(
    db_session,
):
    from sqlalchemy.engine.result import ScalarResult

    model_instances = MockModel.queries.all(db_session)
    assert isinstance(model_instances, ScalarResult)


def test_all_method_sessionless_without_args_returns_scalar_result():
    from sqlalchemy.engine.result import ScalarResult

    model_instances = MockModel.queries.all()
    assert isinstance(model_instances, ScalarResult)


def test_all_method_bound_session_with_to_list_arg_return_list(db_session):
    model_instances = MockModel.queries.all(db_session, to_list=True)
    assert isinstance(model_instances, list)


def test_all_method_sessionless_with_to_list_arg_return_list():
    model_instances = MockModel.queries.all(to_list=True)
    assert isinstance(model_instances, list)


def test_get_method_bound_session_without_search_field_find_obj_by_pk(
    db_session,
):
    id_ = 1
    obj = MockModel.queries.get(id_, db_session)
    assert isinstance(obj, MockModel)
    assert obj.id == id_


def test_get_method_sessionless_without_search_field_find_obj_by_pk():
    id_ = 1
    obj = MockModel.queries.get(id_)
    assert isinstance(obj, MockModel)
    assert obj.id == id_


def test_get_method_bound_session_with_name_search_field_find_obj_by_name(
    db_session,
):
    name = "obj1"
    obj = MockModel.queries.get(
        value="obj1", session=db_session, search_field="name"
    )
    assert obj.name == name


def test_teardown(db_session):
    MockBase.metadata.drop_all(bind=test_engine)
