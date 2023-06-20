import datetime as dt

import pytest
from sqlalchemy.engine.result import ScalarResult

from app import settings
from app.utils import today, tomorrow, yesterday

from .fixtures import (
    TestModel,
    create_tables,
    date_manager,
    db_session,
    engine,
    populate_db,
)


def test_first_method_return_first_added_instance(db_session, date_manager):
    db_session.add(TestModel(name="new_obj", created_at=yesterday()))
    db_session.commit()

    first_from_db = date_manager.first()
    assert isinstance(first_from_db, TestModel)
    assert first_from_db.name == "new_obj"


def test_last_method_return_last_added_instance(db_session, date_manager):
    db_session.add(TestModel(name="new_obj", created_at=tomorrow()))
    db_session.commit()

    last_from_db = date_manager.last()
    assert isinstance(last_from_db, TestModel)
    assert last_from_db.name == "new_obj"


def test_first_n_return_given_number_of_first_added_instances(
    db_session, date_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            TestModel(name=test_name, created_at=yesterday())
            for test_name in test_names
        ]
    )
    db_session.commit()

    first_n_from_db = date_manager.first_n(sample_size)
    assert isinstance(first_n_from_db, ScalarResult)

    first_n_from_db = first_n_from_db.all()
    assert len(first_n_from_db) == sample_size

    first_n_names = [obj.name for obj in first_n_from_db]
    assert first_n_names == test_names


def test_first_n_return_empty_result_for_zero_arg(date_manager):
    first_n_from_db = date_manager.first_n(0)
    assert isinstance(first_n_from_db, ScalarResult)
    assert first_n_from_db.all() == []


def test_last_n_return_given_number_of_first_added_instances(
    db_session, date_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            TestModel(name=test_name, created_at=tomorrow())
            for test_name in test_names
        ]
    )
    db_session.commit()

    last_n_from_db = date_manager.last_n(sample_size)
    assert isinstance(last_n_from_db, ScalarResult)

    last_n_from_db = last_n_from_db.all()
    assert len(last_n_from_db) == sample_size

    last_n_names = [obj.name for obj in last_n_from_db]
    assert last_n_names == test_names


def test_last_n_return_empty_result_for_zero_arg(date_manager):
    last_n_from_db = date_manager.last_n(0)
    assert isinstance(last_n_from_db, ScalarResult)
    assert last_n_from_db.all() == []
