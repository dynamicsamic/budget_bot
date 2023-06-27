import datetime as dt

from app import settings


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
    t = now()
    return dt.datetime(year=t.year, month=t.month, day=t.day - 1).astimezone(
        settings.TIME_ZONE
    )


def timed_tomorrow() -> dt.datetime:
    t = now()
    return dt.datetime(year=t.year, month=t.month, day=t.day + 1).astimezone(
        settings.TIME_ZONE
    )


def today() -> dt.date:
    return dt.date.today()


def yesterday() -> dt.date:
    return today() - dt.timedelta(days=1)


def tomorrow() -> dt.date:
    return today() + dt.timedelta(days=1)
