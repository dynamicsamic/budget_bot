import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Query

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
    CustomDateTestModel,
    basic_date_manager,
    create_tables,
    custom_date_manager,
    db_session,
    engine,
    populate_db,
)

##############
# TESTS FOR  #
#  DEFUALT   #
#  MANAGERS  #
#    WITH    #
# CREATED_AT #
# DATEFIELD  #
##############


def test_between_return_query_result_with_test_instances(basic_date_manager):
    query = basic_date_manager._between(minute_before_now(), timed_tomorrow())
    assert isinstance(query, Query)
    assert all(isinstance(obj, BaseTestModel) for obj in query)


def test_between_with_broad_gap_return_all_instances(basic_date_manager):
    assert (
        len(
            basic_date_manager._between(
                timed_yesterday(), timed_tomorrow()
            ).all()
        )
        == constants["TEST_SAMPLE_SIZE"]
    )


def test_between_with_narrow_gap_return_empty_query(basic_date_manager):
    assert basic_date_manager._between(now(), now()).all() == []


def test_between_with_tomorrow_gap_return_instances_created_tommorrow(
    db_session, basic_date_manager
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
    query = basic_date_manager._between(tomorrow, overmorrow).all()

    assert len(query) == sample_size

    names_from_query = [obj.name for obj in query]
    assert names_from_query == test_names


def test_between_with_twisted_gap_return_empty_query(basic_date_manager):
    query = basic_date_manager._between(timed_tomorrow(), timed_yesterday())
    assert isinstance(query, Query)
    assert query.all() == []


def test_today_return_instances_created_today(db_session, basic_date_manager):
    initial_num = basic_date_manager.count()
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
    assert len(basic_date_manager.today(dateinfo).all()) == initial_num + 2

    # Instaces created tomorrow and yesterday aren't included in today query.
    db_session.add_all(
        [
            BaseTestModel(name="test01", created_at=timed_tomorrow()),
            BaseTestModel(name="test02", created_at=timed_yesterday()),
        ]
    )
    db_session.commit()
    assert len(basic_date_manager.today(dateinfo).all()) == initial_num + 2

    # Check all instances were added.
    assert basic_date_manager.count() == initial_num + 4


@pytest.mark.current
def test_yesterday_return_instances_created_yesterday(
    db_session, basic_date_manager
):
    initial_num = basic_date_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    yesterday = timed_yesterday()
    dateinfo = DateGen(now())

    created_yesterday = [
        BaseTestModel(
            name="yesterday",
            created_at=yesterday,
        ),
        BaseTestModel(
            name="yesterday_start",
            created_at=yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
        ),
        BaseTestModel(
            name="yesterday_end",
            created_at=yesterday.replace(
                hour=23,
                minute=59,
                second=5,
                microsecond=999999,
            ),
        ),
    ]
    db_session.add_all(created_yesterday)
    db_session.commit()

    assert len(basic_date_manager.yesterday(dateinfo).all()) == len(
        created_yesterday
    )

    # Instaces created 2 days ago or tomorrow
    # aren't included in yesterday query
    db_session.add_all(
        [
            BaseTestModel(
                name="two_days_ago",
                created_at=yesterday - dt.timedelta(days=1),
            ),
            BaseTestModel(
                name="tomorrow",
                created_at=yesterday + dt.timedelta(days=2),
            ),
        ]
    )
    db_session.commit()
    assert len(basic_date_manager.yesterday(dateinfo).all()) == len(
        created_yesterday
    )

    # Check all instances were added.
    assert basic_date_manager.count() == initial_num + 5


def test_this_year_return_instances_created_within_this_year(
    db_session, basic_date_manager
):
    initial_num = basic_date_manager.count()
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
    assert len(basic_date_manager.this_year(dateinfo).all()) == initial_num + 5

    # Instaces created last or next year aren't included in this year query
    db_session.add_all(
        [
            BaseTestModel(
                name="test1",
                created_at=datetime - dt.timedelta(days=366),
            ),
            BaseTestModel(
                name="test2",
                created_at=datetime + dt.timedelta(days=366),
            ),
        ]
    )
    db_session.commit()
    assert len(basic_date_manager.this_year(dateinfo).all()) == initial_num + 5

    # Check all instances were added.
    assert basic_date_manager.count() == initial_num + 7


def test_this_month_return_instances_created_within_this_month(
    db_session, basic_date_manager
):
    initial_num = basic_date_manager.count()
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
        len(basic_date_manager.this_month(dateinfo).all()) == initial_num + 5
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
        len(basic_date_manager.this_month(dateinfo).all()) == initial_num + 5
    )

    # Check all instances were added.
    assert basic_date_manager.count() == initial_num + 7


def test_this_week_return_instances_created_within_this_week(
    db_session, basic_date_manager
):
    initial_num = basic_date_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = dt.datetime(
        year=2023,
        month=7,
        day=5,
    )

    created_this_week = [
        BaseTestModel(name="today", created_at=datetime),
        BaseTestModel(
            name="tomorrow", created_at=datetime + dt.timedelta(days=1)
        ),
        BaseTestModel(
            name="yesterday", created_at=datetime - dt.timedelta(days=1)
        ),
        BaseTestModel(
            name="weekstart",
            created_at=datetime.replace(
                day=3, hour=0, minute=0, second=0, microsecond=0
            ),
        ),
        BaseTestModel(
            name="weekend",
            created_at=datetime.replace(
                day=9,
                hour=23,
                minute=59,
                second=5,
                microsecond=999999,
            ),
        ),
    ]
    db_session.add_all(created_this_week)
    db_session.commit()

    dateinfo = DateGen(datetime)

    assert len(basic_date_manager.this_week(dateinfo).all()) == len(
        created_this_week
    )

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
    assert len(basic_date_manager.this_week(dateinfo).all()) == len(
        created_this_week
    )

    # Check all instances were added.
    assert basic_date_manager.count() == initial_num + 7


@pytest.mark.current
def test_yesterday_return_instances_created_yesterday(
    db_session, basic_date_manager
):
    initial_num = basic_date_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    yesterday = timed_yesterday()
    dateinfo = DateGen(now())

    created_yesterday = [
        BaseTestModel(
            name="yesterday",
            created_at=yesterday,
        ),
        BaseTestModel(
            name="yesterday_start",
            created_at=yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
        ),
        BaseTestModel(
            name="yesterday_end",
            created_at=yesterday.replace(
                hour=23,
                minute=59,
                second=5,
                microsecond=999999,
            ),
        ),
    ]
    db_session.add_all(created_yesterday)
    db_session.commit()

    assert len(basic_date_manager.yesterday(dateinfo).all()) == len(
        created_yesterday
    )

    # Instaces created 2 days ago or tomorrow
    # aren't included in yesterday query
    db_session.add_all(
        [
            BaseTestModel(
                name="two_days_ago",
                created_at=yesterday - dt.timedelta(days=1),
            ),
            BaseTestModel(
                name="tomorrow",
                created_at=yesterday + dt.timedelta(days=2),
            ),
        ]
    )
    db_session.commit()
    assert len(basic_date_manager.yesterday(dateinfo).all()) == len(
        created_yesterday
    )

    # Check all instances were added.
    assert basic_date_manager.count() == initial_num + 5


#############
# TESTS FOR #
# MANAGERS  #
#   WITH    #
#  CUSTOM   #
# DATEFIELD #
#############


def test_today_return_instances_selected_by_custom_datefield(
    db_session, custom_date_manager
):
    initial_num = custom_date_manager.count()
    assert initial_num == 0

    datetime = now()
    dateinfo = DateGen(datetime)

    # Add instances created_yesterday, but have today's datefield
    db_session.add_all(
        [
            CustomDateTestModel(
                name="test1",
                custom_datefield=datetime,
                created_at=timed_yesterday(),
            ),
            CustomDateTestModel(
                name="test2",
                custom_datefield=datetime,
                created_at=timed_yesterday(),
            ),
        ]
    )
    db_session.commit()
    assert len(custom_date_manager.today(dateinfo).all()) == initial_num + 2

    # Instaces with tomorrow and yesterday dates aren't included in
    # today query.
    db_session.add_all(
        [
            CustomDateTestModel(
                name="test01", custom_datefield=timed_yesterday()
            ),
            CustomDateTestModel(
                name="test02", custom_datefield=timed_tomorrow()
            ),
        ]
    )
    db_session.commit()
    assert len(custom_date_manager.today(dateinfo).all()) == initial_num + 2

    # Check all instances were added.
    assert custom_date_manager.count() == initial_num + 4


def test_this_year_return_instances_selected_by_custom_field(
    db_session, custom_date_manager
):
    initial_num = custom_date_manager.count()
    assert initial_num == 0

    datetime = now()
    dateinfo = DateGen(datetime)
    last_year = datetime - dt.timedelta(days=366)

    # All instances have `created_at` field set to last year
    # to show that `custom_datefield` used instead.
    added_this_year = [
        CustomDateTestModel(name="now", created_at=last_year),
        CustomDateTestModel(
            name="tomorrow",
            custom_datefield=timed_tomorrow(),
            created_at=last_year,
        ),
        CustomDateTestModel(
            name="yesterday",
            custom_datefield=timed_yesterday(),
            created_at=last_year,
        ),
        CustomDateTestModel(
            name="yearstart",
            custom_datefield=datetime.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            ),
            created_at=last_year,
        ),
        CustomDateTestModel(
            name="yearend",
            custom_datefield=datetime.replace(
                month=12,
                day=31,
                hour=23,
                minute=59,
                second=59,
                microsecond=999999,
            ),
            created_at=last_year,
        ),
    ]
    db_session.add_all(added_this_year)
    db_session.commit()
    assert (
        len(custom_date_manager.this_year(dateinfo).all()) == initial_num + 5
    )

    # Instaces with last or next year custom_datefield
    # aren't included in this year query
    db_session.add_all(
        [
            CustomDateTestModel(
                name="last_year",
                custom_datefield=datetime - dt.timedelta(days=366),
            ),
            CustomDateTestModel(
                name="next_year",
                custom_datefield=datetime + dt.timedelta(days=366),
            ),
        ]
    )
    db_session.commit()
    assert (
        len(custom_date_manager.this_year(dateinfo).all()) == initial_num + 5
    )

    # Check all instances were added.
    assert custom_date_manager.count() == initial_num + 7


def test_this_month_return_instances_selected_by_custom_field(
    db_session, custom_date_manager
):
    initial_num = custom_date_manager.count()
    assert initial_num == 0

    datetime = now().replace(day=15)  # set middlemonth
    dateinfo = DateGen(datetime)
    last_month = datetime - dt.timedelta(days=20)

    # All instances have `created_at` field set to last month
    # to show that `custom_datefield` used instead.
    added_this_month = [
        CustomDateTestModel(name="now", created_at=last_month),
        CustomDateTestModel(
            name="tomorrow",
            custom_datefield=timed_tomorrow(),
            created_at=last_month,
        ),
        CustomDateTestModel(
            name="yesterday",
            custom_datefield=timed_yesterday(),
            created_at=last_month,
        ),
        CustomDateTestModel(
            name="month_start",
            custom_datefield=datetime.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ),
            created_at=last_month,
        ),
        CustomDateTestModel(
            name="month_end",
            custom_datefield=datetime.replace(
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
            created_at=last_month,
        ),
    ]
    db_session.add_all(added_this_month)
    db_session.commit()
    assert (
        len(custom_date_manager.this_month(dateinfo).all()) == initial_num + 5
    )

    # Instaces with last or next month custom_datefield
    # aren't included in this month query
    db_session.add_all(
        [
            CustomDateTestModel(
                name="last_month",
                custom_datefield=datetime - dt.timedelta(days=31),
            ),
            CustomDateTestModel(
                name="next_month",
                custom_datefield=datetime + dt.timedelta(days=31),
            ),
        ]
    )
    db_session.commit()
    assert (
        len(custom_date_manager.this_month(dateinfo).all()) == initial_num + 5
    )

    # Check all instances were added.
    assert custom_date_manager.count() == initial_num + 7


def test_this_week_return_instances_selected_by_custom_field(
    db_session, custom_date_manager
):
    initial_num = custom_date_manager.count()
    assert initial_num == 0

    datetime = dt.datetime(
        year=2023,
        month=7,
        day=5,
    )
    dateinfo = DateGen(datetime)
    last_week = datetime - dt.timedelta(weeks=1)

    # All instances have `created_at` field set to last week
    # to show that `custom_datefield` used instead.
    added_this_week = [
        CustomDateTestModel(
            name="today", custom_datefield=datetime, created_at=last_week
        ),
        CustomDateTestModel(
            name="tomorrow",
            custom_datefield=datetime + dt.timedelta(days=1),
            created_at=last_week,
        ),
        CustomDateTestModel(
            name="yesterday",
            custom_datefield=datetime - dt.timedelta(days=1),
            created_at=last_week,
        ),
        CustomDateTestModel(
            name="week_start",
            custom_datefield=datetime.replace(
                day=3, hour=0, minute=0, second=0, microsecond=0
            ),
            created_at=last_week,
        ),
        CustomDateTestModel(
            name="week_end",
            custom_datefield=datetime.replace(
                day=9,
                hour=23,
                minute=59,
                second=5,
                microsecond=999999,
            ),
            created_at=last_week,
        ),
    ]
    db_session.add_all(added_this_week)
    db_session.commit()

    assert len(custom_date_manager.this_week(dateinfo).all()) == len(
        added_this_week
    )

    # Instaces with last or next week custom_datefield
    # aren't included in this week query
    db_session.add_all(
        [
            CustomDateTestModel(
                name="last_week",
                custom_datefield=datetime - dt.timedelta(weeks=1),
            ),
            CustomDateTestModel(
                name="next_week",
                custom_datefield=datetime + dt.timedelta(weeks=1),
            ),
        ]
    )
    db_session.commit()
    assert len(custom_date_manager.this_week(dateinfo).all()) == len(
        added_this_week
    )

    # Check all instances were added.
    assert custom_date_manager.count() == initial_num + 7


def test_yesterday_return_instances_selected_by_custom_field(
    db_session, custom_date_manager
):
    initial_num = custom_date_manager.count()
    assert initial_num == 0

    yesterday = timed_yesterday()
    dateinfo = DateGen(now())
    two_days_ago = yesterday - dt.timedelta(days=1)

    # All instances have `created_at` field set to two days ago
    # to show that `custom_datefield` used instead.
    added_yesterday = [
        CustomDateTestModel(
            name="yesterday",
            custom_datefield=yesterday,
            created_at=two_days_ago,
        ),
        CustomDateTestModel(
            name="yesterday_start",
            custom_datefield=yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
            created_at=two_days_ago,
        ),
        CustomDateTestModel(
            name="yesterday_end",
            custom_datefield=yesterday.replace(
                hour=23,
                minute=59,
                second=5,
                microsecond=999999,
            ),
            created_at=two_days_ago,
        ),
    ]
    db_session.add_all(added_yesterday)
    db_session.commit()

    assert len(custom_date_manager.yesterday(dateinfo).all()) == len(
        added_yesterday
    )

    # Instaces with 2 days ago or tomorrow custom_datefield
    # aren't included in yesterday query
    db_session.add_all(
        [
            CustomDateTestModel(
                name="two_days_ago",
                custom_datefield=yesterday - dt.timedelta(days=1),
            ),
            CustomDateTestModel(
                name="tomorrow",
                custom_datefield=yesterday + dt.timedelta(days=2),
            ),
        ]
    )
    db_session.commit()
    assert len(custom_date_manager.yesterday(dateinfo).all()) == len(
        added_yesterday
    )

    # Check all instances were added.
    assert custom_date_manager.count() == initial_num + 5
