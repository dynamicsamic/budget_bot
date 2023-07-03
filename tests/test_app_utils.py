import datetime as dt

import pytest

from app.utils import DateGen

full_month_date = dt.date(year=2023, month=7, day=14)
leap_year_date = dt.date(year=2020, month=2, day=29)
february_29th = dt.date(year=2020, month=2, day=29)


@pytest.mark.current
def test_flow_date_gen_with_full_month_date():
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
