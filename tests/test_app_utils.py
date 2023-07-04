import datetime as dt

import pytest

from app.utils import DateGen

full_month_date = dt.date(year=2023, month=7, day=14)
short_month_date = dt.date(year=2023, month=6, day=15)
february_29th = dt.date(year=2020, month=2, day=29)
february_28th = dt.date(year=2023, month=2, day=28)
january_1st = dt.date(year=2023, month=1, day=1)
december_31st = dt.date(year=2023, month=12, day=31)


@pytest.mark.current
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


@pytest.mark.current
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


@pytest.mark.current
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


@pytest.mark.current
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


@pytest.mark.current
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


@pytest.mark.current
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
