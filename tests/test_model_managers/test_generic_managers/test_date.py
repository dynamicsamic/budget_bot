import datetime as dt

from sqlalchemy.orm import Query

from app.utils import (
    DateGen,
    minute_before_now,
    now,
    timed_tomorrow,
    timed_yesterday,
)
from tests.conf import constants

from .fixtures import (
    GenericTestModel,
    create_tables,
    custom_datefield_manager,
    db_session,
    default_datefield_manager,
    engine,
    generic_manager,
    populate_tables,
)

##############
# TESTS FOR  #
#  DEFUALT   #
#  MANAGERS  #
#    WITH    #
# CREATED_AT #
# DATEFIELD  #
##############


def test_between_return_query_result_with_test_instances(
    default_datefield_manager,
):
    query = default_datefield_manager._between(
        minute_before_now(), timed_tomorrow()
    )
    assert isinstance(query, Query)
    assert all(isinstance(obj, GenericTestModel) for obj in query)


def test_between_with_broad_gap_return_all_instances(
    default_datefield_manager,
):
    assert (
        default_datefield_manager._between(
            timed_yesterday(), timed_tomorrow()
        ).count()
        == constants["TEST_SAMPLE_SIZE"]
    )


def test_between_with_narrow_gap_return_empty_query(default_datefield_manager):
    assert default_datefield_manager._between(now(), now()).all() == []


def test_between_with_tomorrow_gap_return_instances_created_tommorrow(
    db_session, default_datefield_manager
):
    tomorrow = timed_tomorrow()
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            GenericTestModel(name=test_name, created_at=tomorrow)
            for test_name in test_names
        ]
    )
    db_session.commit()

    overmorrow = tomorrow + dt.timedelta(days=1)
    query = default_datefield_manager._between(tomorrow, overmorrow).all()

    assert len(query) == sample_size

    names_from_query = [obj.name for obj in query]
    assert names_from_query == test_names


def test_between_with_twisted_gap_return_empty_query(
    default_datefield_manager,
):
    query = default_datefield_manager._between(
        timed_tomorrow(), timed_yesterday()
    )
    assert isinstance(query, Query)
    assert query.all() == []


def test_today_return_instances_created_today(
    db_session, default_datefield_manager
):
    initial_num = default_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = now()
    dateinfo = DateGen(datetime)

    db_session.add_all(
        [
            GenericTestModel(
                name="test1",
                created_at=datetime.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
            ),
            GenericTestModel(
                name="test2",
                created_at=datetime.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                ),
            ),
        ]
    )
    db_session.commit()
    assert default_datefield_manager.today(dateinfo).count() == initial_num + 2

    # Instaces created tomorrow and yesterday aren't included in today query.
    db_session.add_all(
        [
            GenericTestModel(name="test01", created_at=timed_tomorrow()),
            GenericTestModel(name="test02", created_at=timed_yesterday()),
        ]
    )
    db_session.commit()
    assert default_datefield_manager.today(dateinfo).count() == initial_num + 2

    # Check all instances were added.
    assert default_datefield_manager.count() == initial_num + 4


def test_yesterday_return_instances_created_yesterday(
    db_session, default_datefield_manager
):
    initial_num = default_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    yesterday = timed_yesterday()
    dateinfo = DateGen(now())

    created_yesterday = [
        GenericTestModel(
            name="yesterday",
            created_at=yesterday,
        ),
        GenericTestModel(
            name="yesterday_start",
            created_at=yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
        ),
        GenericTestModel(
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

    assert default_datefield_manager.yesterday(dateinfo).count() == len(
        created_yesterday
    )

    # Instaces created 2 days ago or tomorrow
    # aren't included in yesterday query
    db_session.add_all(
        [
            GenericTestModel(
                name="two_days_ago",
                created_at=yesterday - dt.timedelta(days=1),
            ),
            GenericTestModel(
                name="tomorrow",
                created_at=yesterday + dt.timedelta(days=2),
            ),
        ]
    )
    db_session.commit()
    assert default_datefield_manager.yesterday(dateinfo).count() == len(
        created_yesterday
    )

    # Check all instances were added.
    assert default_datefield_manager.count() == initial_num + 5


def test_this_year_return_instances_created_within_this_year(
    db_session, default_datefield_manager
):
    initial_num = default_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = now()
    dateinfo = DateGen(datetime)

    db_session.add_all(
        [
            GenericTestModel(name="test1"),
            GenericTestModel(name="test2", created_at=timed_tomorrow()),
            GenericTestModel(name="test3", created_at=timed_yesterday()),
            GenericTestModel(
                name="test4",
                created_at=datetime.replace(
                    month=1, day=1, hour=0, minute=0, second=0, microsecond=0
                ),
            ),
            GenericTestModel(
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
    assert (
        default_datefield_manager.this_year(dateinfo).count()
        == initial_num + 5
    )

    # Instaces created last or next year aren't included in this year query
    db_session.add_all(
        [
            GenericTestModel(
                name="test1",
                created_at=datetime - dt.timedelta(days=366),
            ),
            GenericTestModel(
                name="test2",
                created_at=datetime + dt.timedelta(days=366),
            ),
        ]
    )
    db_session.commit()
    assert (
        default_datefield_manager.this_year(dateinfo).count()
        == initial_num + 5
    )

    # Check all instances were added.
    assert default_datefield_manager.count() == initial_num + 7


def test_this_month_return_instances_created_within_this_month(
    db_session, default_datefield_manager
):
    initial_num = default_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = now().replace(day=15)  # set middlemonth
    dateinfo = DateGen(datetime)

    db_session.add_all(
        [
            GenericTestModel(name="test1"),
            GenericTestModel(name="test2", created_at=timed_tomorrow()),
            GenericTestModel(name="test3", created_at=timed_yesterday()),
            GenericTestModel(
                name="test4",
                created_at=datetime.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                ),
            ),
            GenericTestModel(
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
        default_datefield_manager.this_month(dateinfo).count()
        == initial_num + 5
    )

    # Instaces created last or next month aren't included in this month query
    db_session.add_all(
        [
            GenericTestModel(
                name="test1", created_at=datetime - dt.timedelta(days=31)
            ),
            GenericTestModel(
                name="test2", created_at=datetime + dt.timedelta(days=31)
            ),
        ]
    )
    db_session.commit()
    assert (
        default_datefield_manager.this_month(dateinfo).count()
        == initial_num + 5
    )

    # Check all instances were added.
    assert default_datefield_manager.count() == initial_num + 7


def test_this_week_return_instances_created_within_this_week(
    db_session, default_datefield_manager
):
    initial_num = default_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = dt.datetime(
        year=2023,
        month=7,
        day=5,
    )

    created_this_week = [
        GenericTestModel(name="today", created_at=datetime),
        GenericTestModel(
            name="tomorrow", created_at=datetime + dt.timedelta(days=1)
        ),
        GenericTestModel(
            name="yesterday", created_at=datetime - dt.timedelta(days=1)
        ),
        GenericTestModel(
            name="weekstart",
            created_at=datetime.replace(
                day=3, hour=0, minute=0, second=0, microsecond=0
            ),
        ),
        GenericTestModel(
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

    assert default_datefield_manager.this_week(dateinfo).count() == len(
        created_this_week
    )

    # Instaces created last or next week aren't included in this week query
    db_session.add_all(
        [
            GenericTestModel(
                name="test1",
                created_at=datetime - dt.timedelta(weeks=1),
            ),
            GenericTestModel(
                name="test2",
                created_at=datetime + dt.timedelta(weeks=1),
            ),
        ]
    )
    db_session.commit()
    assert default_datefield_manager.this_week(dateinfo).count() == len(
        created_this_week
    )

    # Check all instances were added.
    assert default_datefield_manager.count() == initial_num + 7


def test_yesterday_return_instances_created_yesterday(
    db_session, default_datefield_manager
):
    initial_num = default_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    yesterday = timed_yesterday()
    dateinfo = DateGen(now())

    created_yesterday = [
        GenericTestModel(
            name="yesterday",
            created_at=yesterday,
        ),
        GenericTestModel(
            name="yesterday_start",
            created_at=yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
        ),
        GenericTestModel(
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

    assert default_datefield_manager.yesterday(dateinfo).count() == len(
        created_yesterday
    )

    # Instaces created 2 days ago or tomorrow
    # aren't included in yesterday query
    db_session.add_all(
        [
            GenericTestModel(
                name="two_days_ago",
                created_at=yesterday - dt.timedelta(days=1),
            ),
            GenericTestModel(
                name="tomorrow",
                created_at=yesterday + dt.timedelta(days=2),
            ),
        ]
    )
    db_session.commit()
    assert default_datefield_manager.yesterday(dateinfo).count() == len(
        created_yesterday
    )

    # Check all instances were added.
    assert default_datefield_manager.count() == initial_num + 5


#############
# TESTS FOR #
# MANAGERS  #
#   WITH    #
#  CUSTOM   #
# DATEFIELD #
#############


def test_today_return_instances_selected_by_custom_datefield(
    db_session, custom_datefield_manager
):
    initial_num = custom_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = now()
    dateinfo = DateGen(datetime)

    # Add instances created_yesterday, but have today's datefield
    db_session.add_all(
        [
            GenericTestModel(
                name="test1",
                custom_datefield=datetime,
                created_at=timed_yesterday(),
            ),
            GenericTestModel(
                name="test2",
                custom_datefield=datetime,
                created_at=timed_yesterday(),
            ),
        ]
    )
    db_session.commit()
    assert custom_datefield_manager.today(dateinfo).count() == initial_num + 2

    # Instaces with tomorrow and yesterday dates aren't included in
    # today query.
    db_session.add_all(
        [
            GenericTestModel(
                name="test01", custom_datefield=timed_yesterday()
            ),
            GenericTestModel(name="test02", custom_datefield=timed_tomorrow()),
        ]
    )
    db_session.commit()
    assert custom_datefield_manager.today(dateinfo).count() == initial_num + 2

    # Check all instances were added.
    assert custom_datefield_manager.count() == initial_num + 4


def test_this_year_return_instances_selected_by_custom_field(
    db_session, custom_datefield_manager
):
    initial_num = custom_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = now()
    dateinfo = DateGen(datetime)
    last_year = datetime - dt.timedelta(days=366)

    # All instances have `created_at` field set to last year
    # to show that `custom_datefield` used instead.
    added_this_year = [
        GenericTestModel(name="now", created_at=last_year),
        GenericTestModel(
            name="tomorrow",
            custom_datefield=timed_tomorrow(),
            created_at=last_year,
        ),
        GenericTestModel(
            name="yesterday",
            custom_datefield=timed_yesterday(),
            created_at=last_year,
        ),
        GenericTestModel(
            name="yearstart",
            custom_datefield=datetime.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            ),
            created_at=last_year,
        ),
        GenericTestModel(
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
        custom_datefield_manager.this_year(dateinfo).count() == initial_num + 5
    )

    # Instaces with last or next year custom_datefield
    # aren't included in this year query
    db_session.add_all(
        [
            GenericTestModel(
                name="last_year",
                custom_datefield=datetime - dt.timedelta(days=366),
            ),
            GenericTestModel(
                name="next_year",
                custom_datefield=datetime + dt.timedelta(days=366),
            ),
        ]
    )
    db_session.commit()
    assert (
        custom_datefield_manager.this_year(dateinfo).count() == initial_num + 5
    )

    # Check all instances were added.
    assert custom_datefield_manager.count() == initial_num + 7


def test_this_month_return_instances_selected_by_custom_field(
    db_session, custom_datefield_manager
):
    initial_num = custom_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    datetime = now().replace(day=15)  # set middlemonth
    dateinfo = DateGen(datetime)
    last_month = datetime - dt.timedelta(days=20)

    # All instances have `created_at` field set to last month
    # to show that `custom_datefield` used instead.
    added_this_month = [
        GenericTestModel(name="now", created_at=last_month),
        GenericTestModel(
            name="tomorrow",
            custom_datefield=timed_tomorrow(),
            created_at=last_month,
        ),
        GenericTestModel(
            name="yesterday",
            custom_datefield=timed_yesterday(),
            created_at=last_month,
        ),
        GenericTestModel(
            name="month_start",
            custom_datefield=datetime.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ),
            created_at=last_month,
        ),
        GenericTestModel(
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
        custom_datefield_manager.this_month(dateinfo).count()
        == initial_num + 5
    )

    # Instaces with last or next month custom_datefield
    # aren't included in this month query
    db_session.add_all(
        [
            GenericTestModel(
                name="last_month",
                custom_datefield=datetime - dt.timedelta(days=31),
            ),
            GenericTestModel(
                name="next_month",
                custom_datefield=datetime + dt.timedelta(days=31),
            ),
        ]
    )
    db_session.commit()
    assert (
        custom_datefield_manager.this_month(dateinfo).count()
        == initial_num + 5
    )

    # Check all instances were added.
    assert custom_datefield_manager.count() == initial_num + 7


def test_this_week_return_instances_selected_by_custom_field(
    db_session, custom_datefield_manager
):
    initial_num = custom_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

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
        GenericTestModel(
            name="today", custom_datefield=datetime, created_at=last_week
        ),
        GenericTestModel(
            name="tomorrow",
            custom_datefield=datetime + dt.timedelta(days=1),
            created_at=last_week,
        ),
        GenericTestModel(
            name="yesterday",
            custom_datefield=datetime - dt.timedelta(days=1),
            created_at=last_week,
        ),
        GenericTestModel(
            name="week_start",
            custom_datefield=datetime.replace(
                day=3, hour=0, minute=0, second=0, microsecond=0
            ),
            created_at=last_week,
        ),
        GenericTestModel(
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

    assert custom_datefield_manager.this_week(dateinfo).count() == len(
        added_this_week
    )

    # Instaces with last or next week custom_datefield
    # aren't included in this week query
    db_session.add_all(
        [
            GenericTestModel(
                name="last_week",
                custom_datefield=datetime - dt.timedelta(weeks=1),
            ),
            GenericTestModel(
                name="next_week",
                custom_datefield=datetime + dt.timedelta(weeks=1),
            ),
        ]
    )
    db_session.commit()
    assert custom_datefield_manager.this_week(dateinfo).count() == len(
        added_this_week
    )

    # Check all instances were added.
    assert custom_datefield_manager.count() == initial_num + 7


def test_yesterday_return_instances_selected_by_custom_field(
    db_session, custom_datefield_manager
):
    initial_num = custom_datefield_manager.count()
    assert initial_num == constants["TEST_SAMPLE_SIZE"]

    yesterday = timed_yesterday()
    dateinfo = DateGen(now())
    two_days_ago = yesterday - dt.timedelta(days=1)

    # All instances have `created_at` field set to two days ago
    # to show that `custom_datefield` used instead.
    added_yesterday = [
        GenericTestModel(
            name="yesterday",
            custom_datefield=yesterday,
            created_at=two_days_ago,
        ),
        GenericTestModel(
            name="yesterday_start",
            custom_datefield=yesterday.replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
            created_at=two_days_ago,
        ),
        GenericTestModel(
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

    assert custom_datefield_manager.yesterday(dateinfo).count() == len(
        added_yesterday
    )

    # Instaces with 2 days ago or tomorrow custom_datefield
    # aren't included in yesterday query
    db_session.add_all(
        [
            GenericTestModel(
                name="two_days_ago",
                custom_datefield=yesterday - dt.timedelta(days=1),
            ),
            GenericTestModel(
                name="tomorrow",
                custom_datefield=yesterday + dt.timedelta(days=2),
            ),
        ]
    )
    db_session.commit()
    assert custom_datefield_manager.yesterday(dateinfo).count() == len(
        added_yesterday
    )

    # Check all instances were added.
    assert custom_datefield_manager.count() == initial_num + 5
