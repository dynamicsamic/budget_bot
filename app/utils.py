import calendar
import datetime as dt
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from app import settings

aiogram_log_handler = logging.StreamHandler()
aiogram_log_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - [%(levelname)s] - <%(funcName)s> : %(message)s"
    )
)


class DateRange:
    days_in_month = {
        1: 31,
        2: lambda year: 29 if calendar.isleap(year) else 28,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31,
    }

    def __init__(self, date: dt.date | dt.datetime):
        self.date = date

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.date})"

    @property
    def is_datetime(self) -> bool:
        return isinstance(self.date, dt.datetime)

    @property
    def year(self) -> int:
        return self.date.year

    @property
    def month(self) -> int:
        return self.date.month

    @property
    def year_range(
        self,
    ) -> tuple[dt.date | dt.datetime, dt.date | dt.datetime]:
        return self.year_start, self.year_end

    @property
    def month_range(
        self,
    ) -> tuple[dt.date | dt.datetime, dt.date | dt.datetime]:
        return self.month_start, self.month_end

    @property
    def week_range(
        self,
    ) -> tuple[dt.date | dt.datetime, dt.date | dt.datetime]:
        return self.week_start, self.week_end

    @property
    def today_range(
        self,
    ) -> tuple[dt.datetime, dt.datetime]:
        return self.today_start, self.today_end

    @property
    def yesterday_range(
        self,
    ) -> tuple[dt.datetime, dt.datetime]:
        return self.yesterday_start, self.yesterday_end

    def num_days(self, month_ordinal: int) -> int:
        if month_ordinal == 2:
            return self.days_in_month[month_ordinal](self.year)
        return self.days_in_month.get(month_ordinal, 30)

    @property
    def year_start(self) -> dt.date | dt.datetime:
        year_start_kwargs = {"year": self.year, "month": 1, "day": 1}
        return (
            dt.datetime(**year_start_kwargs)
            if self.is_datetime
            else dt.date(**year_start_kwargs)
        )

    @property
    def year_end(self) -> dt.date | dt.datetime:
        date_kwargs = {"year": self.year, "month": 12, "day": 31}
        datetime_kwargs = {
            "hour": 23,
            "minute": 59,
            "second": 59,
            "microsecond": 999999,
        }
        return (
            dt.datetime(**date_kwargs, **datetime_kwargs)
            if self.is_datetime
            else dt.date(**date_kwargs)
        )

    @property
    def month_start(self) -> dt.date | dt.datetime:
        return self.year_start.replace(month=self.month)

    @property
    def month_end(self) -> dt.date | dt.datetime:
        return self.year_end.replace(
            month=self.month, day=self.num_days(self.month)
        )

    @property
    def week_start(self) -> dt.date | dt.datetime:
        weekday = self.date.weekday()
        return self.today_start - dt.timedelta(days=weekday)

    @property
    def week_end(self) -> dt.date | dt.datetime:
        days_in_week = 6
        weekday = self.date.weekday()
        return self.today_end + dt.timedelta(days=days_in_week - weekday)

    @property
    def today_start(self) -> dt.date | dt.datetime:
        return self.month_start.replace(day=self.date.day)

    @property
    def today_end(self) -> dt.date | dt.datetime:
        return self.month_end.replace(day=self.date.day)

    @property
    def yesterday_start(self) -> dt.date | dt.datetime:
        return self.today_start - dt.timedelta(days=1)

    @property
    def yesterday_end(self) -> dt.date | dt.datetime:
        return self.today_end - dt.timedelta(days=1)


def gen_date(today: dt.date | dt.datetime, date_descr: str):
    if date_descr == "month_start":
        year, month = today.year, today.month
        return dt.date(year=year, month=month, day=1)


def today_(
    timed: bool = False, daytime: str = "current"
) -> dt.date | dt.datetime:
    if timed:
        day = dt.datetime.today().astimezone(settings.TIME_ZONE)

        if daytime == "start":
            return day.replace(hour=0, minute=0, second=0, microsecond=0)
        elif daytime == "end":
            return day.replace(hour=23, minute=59, second=59, microsecond=59)
        elif daytime.isdecimal() and (0 <= int(daytime) <= 23):
            return day.replace(
                hour=int(daytime), minute=0, second=0, microsecond=0
            )
        else:
            return day
    return dt.date.today()


def now() -> dt.datetime:
    return dt.datetime.today().astimezone(settings.TIME_ZONE)


def minute_before_now() -> dt.datetime:
    return now() - dt.timedelta(minutes=1)


def timed_yesterday() -> dt.datetime:
    return now() - dt.timedelta(days=1)


def timed_tomorrow() -> dt.datetime:
    return now() + dt.timedelta(days=1)


def today() -> dt.date:
    return dt.date.today()


def yesterday() -> dt.date:
    return today() - dt.timedelta(days=1)


def tomorrow() -> dt.date:
    return today() + dt.timedelta(days=1)


def epoch_start():
    return dt.datetime(year=1970, month=1, day=1)


def pretty_datetime(datetime: dt.datetime) -> str:
    return f"{datetime:%Y-%m-%d %H:%M:%S}"


def get_locals(
    locls: dict[str, Any], exclude: Iterable[str]
) -> dict[str, Any]:
    return_kwargs = {k: v for k, v in locls.items() if v is not None}
    for item in exclude:
        return_kwargs.pop(item)
    return return_kwargs


def validate_entry_sum(raw_sum: str) -> tuple[int, str]:
    invalid = 0
    if len(raw_sum) >= 20:
        return invalid, "Задано слишком длинное число."
    cleaned_sum = re.sub(",", ".", re.sub("\s", "", raw_sum))
    try:
        valid_float = round(float(cleaned_sum), 2)
    except ValueError:
        error_message = (
            "Неверный формат суммы.\n"
            "Допустимые форматы: 1521; 100,91; 934.2; 1 445.67"
        )
        return invalid, error_message
    validated = int(valid_float * 100)
    if validated == invalid:
        return invalid, "Сумма не может быть равна 0."
    return validated, ""


def validate_entry_date(raw_date: str) -> tuple[dt.datetime | None, str]:
    spaceless_date = re.sub("[ -]", "", raw_date)
    try:
        int(spaceless_date)
    except ValueError:
        error_message = (
            "Недопустимые символы в дате.\nИспользуйте только цифры "
            "и разделители в виде пробела или тире.\n"
            "Допустимые форматы: дд мм гггг, дд-мм-гггг, ддммгггг"
        )
        return None, error_message

    date = {
        "day": int(spaceless_date[0:2]),
        "month": int(spaceless_date[2:4]),
        "year": int(spaceless_date[4::]),
    }
    try:
        valid_datetime = dt.datetime(**date)
    except ValueError:
        error_message = (
            "Дата содержит ошибку.\n" "Исправьте ошибку и повторите ввод."
        )
        return None, error_message

    return valid_datetime.astimezone(settings.TIME_ZONE), ""


@dataclass
class OffsetPaginator:
    callback_prefix: str
    size: int
    page_limit: int = 10
    current_offset: int = field(default=0, init=False)

    def switch_next(self):
        if self.current_offset + self.page_limit >= self.size:
            pass
        else:
            self.current_offset += self.page_limit

    def switch_back(self):
        if self.current_offset - self.page_limit <= 0:
            self.current_offset = 0
        else:
            self.current_offset -= self.page_limit

    @property
    def next_page_offset(self):
        if self.current_offset + self.page_limit >= self.size:
            return
        return self.current_offset + self.page_limit

    @property
    def prev_page_offset(self):
        if self.current_offset - self.page_limit == 0:
            return 0
        elif self.current_offset - self.page_limit < 0:
            return
        return self.current_offset - self.page_limit
