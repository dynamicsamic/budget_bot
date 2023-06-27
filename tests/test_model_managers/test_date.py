import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.orm import Query

from app import settings
from app.utils import minute_before_now, now, timed_tomorrow, timed_yesterday
from tests.conf import constants

from .fixtures import (
    MyTestModel,
    create_tables,
    date_manager,
    db_session,
    engine,
    populate_db,
)


def test_first_method_return_first_added_instance(db_session, date_manager):
    db_session.add(MyTestModel(name="new_obj", created_at=timed_yesterday()))
    db_session.commit()

    first_from_db = date_manager.first()
    assert isinstance(first_from_db, MyTestModel)
    assert first_from_db.name == "new_obj"


def test_last_method_return_last_added_instance(db_session, date_manager):
    db_session.add(MyTestModel(name="new_obj", created_at=timed_tomorrow()))
    db_session.commit()

    last_from_db = date_manager.last()
    assert isinstance(last_from_db, MyTestModel)
    assert last_from_db.name == "new_obj"


def test_first_n_return_given_number_of_first_added_instances(
    db_session, date_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            MyTestModel(name=test_name, created_at=timed_yesterday())
            for test_name in test_names
        ]
    )
    db_session.commit()

    first_n_from_db = date_manager.first_n(sample_size)
    assert isinstance(first_n_from_db, Query)

    first_n_from_db = first_n_from_db.all()
    assert len(first_n_from_db) == sample_size

    first_n_names = [obj.name for obj in first_n_from_db]
    assert first_n_names == test_names


def test_first_n_return_empty_result_for_zero_arg(date_manager):
    first_n_from_db = date_manager.first_n(0)
    assert isinstance(first_n_from_db, Query)
    assert first_n_from_db.all() == []


def test_last_n_return_given_number_of_last_added_instances(
    db_session, date_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            MyTestModel(name=test_name, created_at=timed_tomorrow())
            for test_name in test_names
        ]
    )
    db_session.commit()

    last_n_from_db = date_manager.last_n(sample_size)
    assert isinstance(last_n_from_db, Query)

    last_n_from_db = last_n_from_db.all()
    assert len(last_n_from_db) == sample_size

    last_n_names = [obj.name for obj in last_n_from_db]
    assert last_n_names == test_names


def test_last_n_return_empty_result_for_zero_arg(date_manager):
    last_n_from_db = date_manager.last_n(0)
    assert isinstance(last_n_from_db, Query)
    assert last_n_from_db.all() == []


def test_between_return_query_result_with_test_instances(date_manager):
    query = date_manager.between(minute_before_now(), timed_tomorrow())
    assert isinstance(query, Query)
    assert all(isinstance(obj, MyTestModel) for obj in query)


def test_between_with_broad_gap_return_all_instances(date_manager):
    assert (
        len(date_manager.between(minute_before_now(), timed_tomorrow()).all())
        == constants["TEST_SAMPLE_SIZE"]
    )


def test_between_with_narrow_gap_return_empty_query(date_manager):
    assert date_manager.between(now(), now()).all() == []


def test_between_with_tomorrow_gap_return_instances_created_tommorrow(
    db_session, date_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            MyTestModel(name=test_name, created_at=timed_tomorrow())
            for test_name in test_names
        ]
    )
    db_session.commit()

    tomorrow = timed_tomorrow()
    overmorrow = tomorrow + dt.timedelta(days=1)
    query = date_manager.between(tomorrow, overmorrow).all()

    assert len(query) == sample_size

    names_from_query = [obj.name for obj in query]
    assert names_from_query == test_names


def test_between_with_twisted_gap_return_empty_query(date_manager):
    query = date_manager.between(timed_tomorrow(), timed_yesterday())
    assert isinstance(query, Query)
    assert query.all() == []
