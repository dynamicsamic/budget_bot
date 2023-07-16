import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Query

from app import settings
from app.utils import (
    DateGen,
    minute_before_now,
    now,
    timed_tomorrow,
    timed_yesterday,
    today,
    tomorrow,
    yesterday,
)
from tests.conf import constants

from .fixtures import (
    BaseTestModel,
    create_tables,
    created_at_manager,
    date_manager,
    db_session,
    engine,
    populate_db,
)

##############
# TESTS FOR  #
#  MANAGERS  #
#    WITH    #
# CREATED_AT #
#  ORDERING  #
##############


def test_between_return_query_result_with_test_instances(created_at_manager):
    query = created_at_manager._between(minute_before_now(), timed_tomorrow())
    assert isinstance(query, Query)
    assert all(isinstance(obj, BaseTestModel) for obj in query)


def test_between_with_broad_gap_return_all_instances(created_at_manager):
    assert (
        len(
            created_at_manager._between(
                minute_before_now(), timed_tomorrow()
            ).all()
        )
        == constants["TEST_SAMPLE_SIZE"]
    )


def test_between_with_narrow_gap_return_empty_query(created_at_manager):
    assert created_at_manager._between(now(), now()).all() == []


def test_between_with_tomorrow_gap_return_instances_created_tommorrow(
    db_session, created_at_manager
):
    tomorrow = timed_tomorrow()
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            BaseTestModel(name=test_name, created_at=tomorrow)
            for test_name in test_names
        ]
    )
    db_session.commit()

    overmorrow = tomorrow + dt.timedelta(days=1)
    query = created_at_manager._between(tomorrow, overmorrow).all()

    assert len(query) == sample_size

    names_from_query = [obj.name for obj in query]
    assert names_from_query == test_names


def test_between_with_twisted_gap_return_empty_query(created_at_manager):
    query = created_at_manager._between(timed_tomorrow(), timed_yesterday())
    assert isinstance(query, Query)
    assert query.all() == []


def test_today_return_instances_created_today(db_session, created_at_manager):
    initial_num = created_at_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = now()
    dateinfo = DateGen(datetime)

    db_session.add_all(
        [
            BaseTestModel(
                name="test1",
                created_at=datetime.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
            ),
            BaseTestModel(
                name="test2",
                created_at=datetime.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                ),
            ),
        ]
    )
    db_session.commit()
    assert len(created_at_manager.today(dateinfo).all()) == initial_num + 2

    # Instaces created tomorrow and yesterday aren't included in today query.
    db_session.add_all(
        [
            BaseTestModel(name="test01", created_at=timed_tomorrow()),
            BaseTestModel(name="test02", created_at=timed_yesterday()),
        ]
    )
    db_session.commit()
    assert len(created_at_manager.today(dateinfo).all()) == initial_num + 2

    # Check all instances were added.
    assert created_at_manager.count() == initial_num + 4


def test_this_year_return_instances_created_within_this_year(
    db_session, created_at_manager
):
    initial_num = created_at_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = now()
    dateinfo = DateGen(datetime)

    db_session.add_all(
        [
            BaseTestModel(name="test1"),
            BaseTestModel(name="test2", created_at=timed_tomorrow()),
            BaseTestModel(name="test3", created_at=timed_yesterday()),
            BaseTestModel(
                name="test4",
                created_at=datetime.replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                ),
            ),
            BaseTestModel(
                name="test5",
                created_at=datetime.replace(
                    month=12,
                    day=31,
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=999999,
                ),
            ),
        ]
    )
    db_session.commit()
    assert len(created_at_manager.this_year(dateinfo).all()) == initial_num + 5

    # Instaces created last or next year aren't included in this year query
    db_session.add_all(
        [
            BaseTestModel(
                name="test1",
                created_at=datetime - dt.timedelta(days=365),
            ),
            BaseTestModel(
                name="test2",
                created_at=datetime - dt.timedelta(days=365),
            ),
        ]
    )
    db_session.commit()
    assert len(created_at_manager.this_year(dateinfo).all()) == initial_num + 5

    # Check all instances were added.
    assert created_at_manager.count() == initial_num + 7


def test_this_month_return_instances_created_within_this_month(
    db_session, created_at_manager
):
    initial_num = created_at_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = now().replace(day=15)  # set middlemonth
    dateinfo = DateGen(datetime)

    db_session.add_all(
        [
            BaseTestModel(name="test1"),
            BaseTestModel(name="test2", created_at=timed_tomorrow()),
            BaseTestModel(name="test3", created_at=timed_yesterday()),
            BaseTestModel(
                name="test4",
                created_at=datetime.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                ),
            ),
            BaseTestModel(
                name="test5",
                created_at=datetime.replace(
                    day=30
                    if datetime.month in (4, 6, 9, 11)
                    else 28
                    if datetime.month == 2
                    else 31,
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=999999,
                ),
            ),
        ]
    )
    db_session.commit()
    assert (
        len(created_at_manager.this_month(dateinfo).all()) == initial_num + 5
    )

    # Instaces created last or next month aren't included in this month query
    db_session.add_all(
        [
            BaseTestModel(
                name="test1", created_at=datetime - dt.timedelta(days=31)
            ),
            BaseTestModel(
                name="test2", created_at=datetime + dt.timedelta(days=31)
            ),
        ]
    )
    db_session.commit()
    assert (
        len(created_at_manager.this_month(dateinfo).all()) == initial_num + 5
    )

    # Check all instances were added.
    assert created_at_manager.count() == initial_num + 7


def test_this_week_return_instances_created_within_this_week(
    db_session, created_at_manager
):
    initial_num = created_at_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = dt.datetime(
        year=2023,
        month=7,
        day=5,
    )
    dateinfo = DateGen(datetime)

    db_session.add_all(
        [
            BaseTestModel(name="test1", created_at=datetime),
            BaseTestModel(name="test2", created_at=timed_tomorrow()),
            BaseTestModel(name="test3", created_at=timed_yesterday()),
            BaseTestModel(
                name="test4",
                created_at=datetime.replace(
                    day=3, hour=0, minute=0, second=0, microsecond=0
                ),
            ),
            BaseTestModel(
                name="test5",
                created_at=datetime.replace(
                    day=9,
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=999999,
                ),
            ),
        ]
    )
    db_session.commit()
    assert len(created_at_manager.this_week(dateinfo).all()) == initial_num + 5

    # Instaces created last or next week aren't included in this week query
    db_session.add_all(
        [
            BaseTestModel(
                name="test1",
                created_at=datetime - dt.timedelta(weeks=1),
            ),
            BaseTestModel(
                name="test2",
                created_at=datetime + dt.timedelta(weeks=1),
            ),
        ]
    )
    db_session.commit()
    assert len(created_at_manager.this_week(dateinfo).all()) == initial_num + 5

    # Check all instances were added.
    assert created_at_manager.count() == initial_num + 7


#############
# TESTS FOR #
#  MANAGERS #
#    WITH   #
#    DATE   #
#  ORDERING #
#############


@pytest.mark.current
def test_today_return_instances_with_today_date(db_session, date_manager):
    initial_num = date_manager.count()
    assert initial_num == 0

    date = today()
    dateinfo = DateGen(date)

    # Add instances created_yesterday, but have today's date
    db_session.add_all(
        [
            BaseTestModel(
                name="test1", date=date, created_at=timed_yesterday()
            ),
            BaseTestModel(
                name="test2", date=date, created_at=timed_yesterday()
            ),
        ]
    )
    db_session.commit()
    assert len(date_manager.today(dateinfo).all()) == initial_num + 2

    # Instaces with tomorrow and yesterday dates aren't included in
    # today query.
    db_session.add_all(
        [
            BaseTestModel(name="test01", date=yesterday()),
            BaseTestModel(name="test02", date=tomorrow()),
        ]
    )
    db_session.commit()

    assert len(date_manager.today(dateinfo).all()) == initial_num + 2

    # Check all instances were added.
    assert date_manager.count() == initial_num + 4
