import datetime as dt

from app import settings


def today() -> dt.datetime:
    return dt.datetime.today().astimezone(settings.TIME_ZONE)


def yesterday() -> dt.datetime:
    t = today()
    return dt.datetime(year=t.year, month=t.month, day=t.day - 1).astimezone(
        settings.TIME_ZONE
    )


def tomorrow() -> dt.datetime:
    t = today()
    return dt.datetime(year=t.year, month=t.month, day=t.day + 1).astimezone(
        settings.TIME_ZONE
    )
