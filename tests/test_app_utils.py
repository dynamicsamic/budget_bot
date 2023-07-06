import datetime as dt

import pytest

from app.utils import DateGen

full_month_date = dt.date(year=2023, month=7, day=14)
short_month_date = dt.date(year=2023, month=6, day=15)
february_29th = dt.date(year=2020, month=2, day=29)
february_28th = dt.date(year=2023, month=2, day=28)
january_1st = dt.date(year=2023, month=1, day=1)
december_31st = dt.date(year=2023, month=12, day=31)


def test_flow_date_gen_for_full_month_date():
    dgen = DateGen(full_month_date)
    assert dgen.date == full_month_date
    assert dgen.year == full_month_date.year
    assert dgen.month == full_month_date.month
    assert dgen.year_start == full_month_date.replace(month=1, day=1)
    assert dgen.year_end == full_month_date.replace(month=12, day=31)
    assert dgen.year_range == (
        full_month_date.replace(month=1, day=1),
        full_month_date.replace(month=12, day=31),
    )
    assert dgen.month_start == full_month_date.replace(day=1)
    assert dgen.month_end == full_month_date.replace(day=31)
    assert dgen.month_range == (
        full_month_date.replace(day=1),
        full_month_date.replace(day=31),
    )
    assert dgen.week_start == full_month_date.replace(day=10)
    assert dgen.week_end == full_month_date.replace(day=16)
    assert dgen.week_range == (
        full_month_date.replace(day=10),
        full_month_date.replace(day=16),
    )


def test_flow_date_gen_for_short_month_date():
    dgen = DateGen(short_month_date)
    assert dgen.date == short_month_date
    assert dgen.year == short_month_date.year
    assert dgen.month == short_month_date.month
    assert dgen.year_start == short_month_date.replace(month=1, day=1)
    assert dgen.year_end == short_month_date.replace(month=12, day=31)
    assert dgen.year_range == (
        short_month_date.replace(month=1, day=1),
        short_month_date.replace(month=12, day=31),
    )
    assert dgen.month_start == short_month_date.replace(day=1)
    assert dgen.month_end == short_month_date.replace(day=30)
    assert dgen.month_range == (
        short_month_date.replace(day=1),
        short_month_date.replace(day=30),
    )
    assert dgen.week_start == short_month_date.replace(day=12)
    assert dgen.week_end == short_month_date.replace(day=18)
    assert dgen.week_range == (
        short_month_date.replace(day=12),
        short_month_date.replace(day=18),
    )


def test_flow_date_gen_for_february_29th():
    dgen = DateGen(february_29th)
    assert dgen.date == february_29th
    assert dgen.year == february_29th.year
    assert dgen.month == february_29th.month
    assert dgen.year_start == february_29th.replace(month=1, day=1)
    assert dgen.year_end == february_29th.replace(month=12, day=31)
    assert dgen.year_range == (
        february_29th.replace(month=1, day=1),
        february_29th.replace(month=12, day=31),
    )
    assert dgen.month_start == february_29th.replace(day=1)
    assert dgen.month_end == february_29th.replace(day=29)
    assert dgen.month_range == (
        february_29th.replace(day=1),
        february_29th.replace(day=29),
    )
    assert dgen.week_start == february_29th.replace(day=24)
    assert dgen.week_end == february_29th.replace(month=3, day=1)
    assert dgen.week_range == (
        february_29th.replace(day=24),
        february_29th.replace(month=3, day=1),
    )


def test_flow_date_gen_for_february_28th():
    dgen = DateGen(february_28th)
    assert dgen.date == february_28th
    assert dgen.year == february_28th.year
    assert dgen.month == february_28th.month
    assert dgen.year_start == february_28th.replace(month=1, day=1)
    assert dgen.year_end == february_28th.replace(month=12, day=31)
    assert dgen.year_range == (
        february_28th.replace(month=1, day=1),
        february_28th.replace(month=12, day=31),
    )
    assert dgen.month_start == february_28th.replace(day=1)
    assert dgen.month_end == february_28th.replace(day=28)
    assert dgen.month_range == (
        february_28th.replace(day=1),
        february_28th.replace(day=28),
    )
    assert dgen.week_start == february_28th.replace(day=27)
    assert dgen.week_end == february_28th.replace(month=3, day=5)
    assert dgen.week_range == (
        february_28th.replace(day=27),
        february_28th.replace(month=3, day=5),
    )


def test_flow_date_gen_for_janury_1st():
    dgen = DateGen(january_1st)
    assert dgen.date == january_1st
    assert dgen.year == january_1st.year
    assert dgen.month == january_1st.month
    assert dgen.year_start == january_1st
    assert dgen.year_end == january_1st.replace(month=12, day=31)
    assert dgen.year_range == (
        january_1st,
        january_1st.replace(month=12, day=31),
    )
    assert dgen.month_start == january_1st
    assert dgen.month_end == january_1st.replace(day=31)
    assert dgen.month_range == (
        january_1st,
        january_1st.replace(day=31),
    )
    assert dgen.week_start == january_1st.replace(year=2022, month=12, day=26)
    assert dgen.week_end == january_1st
    assert dgen.week_range == (
        january_1st.replace(year=2022, month=12, day=26),
        january_1st,
    )


def test_flow_date_gen_for_december_31st():
    dgen = DateGen(december_31st)
    assert dgen.date == december_31st
    assert dgen.year == december_31st.year
    assert dgen.month == december_31st.month
    assert dgen.year_start == december_31st.replace(month=1, day=1)
    assert dgen.year_end == december_31st
    assert dgen.year_range == (
        december_31st.replace(month=1, day=1),
        december_31st,
    )
    assert dgen.month_start == december_31st.replace(day=1)
    assert dgen.month_end == december_31st
    assert dgen.month_range == (
        december_31st.replace(day=1),
        december_31st,
    )
    assert dgen.week_start == december_31st.replace(day=25)
    assert dgen.week_end == december_31st
    assert dgen.week_range == (
        december_31st.replace(day=25),
        december_31st,
    )


def test_date_year_range_calculate_correctly_for_all_months():
    for i in range(1, 13):
        date = dt.date(year=2023, month=i, day=1)
        dgen = DateGen(date)
        assert dgen.year_start == date.replace(month=1, day=1)
        assert dgen.year_end == date.replace(month=12, day=31)
        assert dgen.year_range == (
            date.replace(month=1, day=1),
            date.replace(month=12, day=31),
        )


def test_date_month_range_calculate_correctly_for_full_months():
    full_month_ordinal = (1, 3, 5, 7, 8, 10, 12)
    for month in full_month_ordinal:
        date = dt.date(year=2023, month=month, day=10)
        dgen = DateGen(date)
        assert dgen.month_start == date.replace(day=1)
        assert dgen.month_end == date.replace(day=31)
        assert dgen.month_range == (date.replace(day=1), date.replace(day=31))


def test_date_month_range_calculate_correctly_for_short_months():
    short_month_ordinal = (4, 6, 9, 11)
    for month in short_month_ordinal:
        date = dt.date(year=2023, month=month, day=10)
        dgen = DateGen(date)
        assert dgen.month_start == date.replace(day=1)
        assert dgen.month_end == date.replace(day=30)
        assert dgen.month_range == (date.replace(day=1), date.replace(day=30))


date_week_ranges = (
    (
        dt.date(year=2023, month=1, day=10),
        dt.date(year=2023, month=1, day=9),
        dt.date(year=2023, month=1, day=15),
    ),
    (
        dt.date(year=2023, month=2, day=17),
        dt.date(year=2023, month=2, day=13),
        dt.date(year=2023, month=2, day=19),
    ),
    (
        dt.date(year=2023, month=3, day=8),
        dt.date(year=2023, month=3, day=6),
        dt.date(year=2023, month=3, day=12),
    ),
    (
        dt.date(year=2023, month=4, day=1),
        dt.date(year=2023, month=3, day=27),
        dt.date(year=2023, month=4, day=2),
    ),
    (
        dt.date(year=2023, month=5, day=9),
        dt.date(year=2023, month=5, day=8),
        dt.date(year=2023, month=5, day=14),
    ),
    (
        dt.date(year=2023, month=6, day=12),
        dt.date(year=2023, month=6, day=12),
        dt.date(year=2023, month=6, day=18),
    ),
    (
        dt.date(year=2023, month=7, day=23),
        dt.date(year=2023, month=7, day=17),
        dt.date(year=2023, month=7, day=23),
    ),
    (
        dt.date(year=2023, month=8, day=11),
        dt.date(year=2023, month=8, day=7),
        dt.date(year=2023, month=8, day=13),
    ),
    (
        dt.date(year=2023, month=9, day=21),
        dt.date(year=2023, month=9, day=18),
        dt.date(year=2023, month=9, day=24),
    ),
    (
        dt.date(year=2023, month=10, day=4),
        dt.date(year=2023, month=10, day=2),
        dt.date(year=2023, month=10, day=8),
    ),
    (
        dt.date(year=2023, month=11, day=28),
        dt.date(year=2023, month=11, day=27),
        dt.date(year=2023, month=12, day=3),
    ),
    (
        dt.date(year=2023, month=12, day=30),
        dt.date(year=2023, month=12, day=25),
        dt.date(year=2023, month=12, day=31),
    ),
)
week_range_test_ids = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)


@pytest.mark.parametrize(
    "date,week_start,week_end", date_week_ranges, ids=week_range_test_ids
)
def test_date_week_range_calculate_correctly_for_all_months(
    date, week_start, week_end
):
    dgen = DateGen(date)
    assert dgen.week_range == (week_start, week_end)


end_of_the_day = {
    "hour": 23,
    "minute": 59,
    "second": 59,
    "microsecond": 999999,
}


@pytest.mark.current
def test_datetime_year_range_calculate_correctly_for_all_months():
    for i in range(1, 13):
        datetime = dt.datetime(year=2023, month=i, day=1)
        dgen = DateGen(datetime)
        assert dgen.year_start == datetime.replace(month=1, day=1)
        assert dgen.year_end == datetime.replace(
            month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
        )
        assert dgen.year_range == (
            datetime.replace(month=1, day=1),
            datetime.replace(month=12, day=31, **end_of_the_day),
        )


@pytest.mark.current
def test_datetim_month_range_calculate_correctly_for_full_months():
    full_month_ordinal = (1, 3, 5, 7, 8, 10, 12)
    for month in full_month_ordinal:
        datetime = dt.datetime(year=2023, month=month, day=10)
        dgen = DateGen(datetime)
        assert dgen.month_start == datetime.replace(day=1)
        assert dgen.month_end == datetime.replace(day=31, **end_of_the_day)
        assert dgen.month_range == (
            datetime.replace(day=1),
            datetime.replace(day=31, **end_of_the_day),
        )


@pytest.mark.current
def test_datetime_month_range_calculate_correctly_for_short_months():
    short_month_ordinal = (4, 6, 9, 11)
    for month in short_month_ordinal:
        datetime = dt.datetime(year=2023, month=month, day=10)
        dgen = DateGen(datetime)
        assert dgen.month_start == datetime.replace(day=1)
        assert dgen.month_end == datetime.replace(day=30, **end_of_the_day)
        assert dgen.month_range == (
            datetime.replace(day=1),
            datetime.replace(day=30, **end_of_the_day),
        )


datetime_week_ranges = (
    (
        dt.datetime(year=2023, month=1, day=10),
        dt.datetime(year=2023, month=1, day=9),
        dt.datetime(year=2023, month=1, day=15, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=2, day=17),
        dt.datetime(year=2023, month=2, day=13),
        dt.datetime(year=2023, month=2, day=19, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=3, day=8),
        dt.datetime(year=2023, month=3, day=6),
        dt.datetime(year=2023, month=3, day=12, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=4, day=1),
        dt.datetime(year=2023, month=3, day=27),
        dt.datetime(year=2023, month=4, day=2, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=5, day=9),
        dt.datetime(year=2023, month=5, day=8),
        dt.datetime(year=2023, month=5, day=14, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=6, day=12),
        dt.datetime(year=2023, month=6, day=12),
        dt.datetime(year=2023, month=6, day=18, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=7, day=23),
        dt.datetime(year=2023, month=7, day=17),
        dt.datetime(year=2023, month=7, day=23, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=8, day=11),
        dt.datetime(year=2023, month=8, day=7),
        dt.datetime(year=2023, month=8, day=13, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=9, day=21),
        dt.datetime(year=2023, month=9, day=18),
        dt.datetime(year=2023, month=9, day=24, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=10, day=4),
        dt.datetime(year=2023, month=10, day=2),
        dt.datetime(year=2023, month=10, day=8, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=11, day=28),
        dt.datetime(year=2023, month=11, day=27),
        dt.datetime(year=2023, month=12, day=3, **end_of_the_day),
    ),
    (
        dt.datetime(year=2023, month=12, day=30),
        dt.datetime(year=2023, month=12, day=25),
        dt.datetime(year=2023, month=12, day=31, **end_of_the_day),
    ),
)


@pytest.mark.current
@pytest.mark.parametrize(
    "datetime,week_start,week_end",
    datetime_week_ranges,
    ids=week_range_test_ids,
)
def test_datetime_week_range_calculate_correctly_for_all_months(
    datetime, week_start, week_end
):
    dgen = DateGen(datetime)
    assert dgen.week_range == (week_start, week_end)
