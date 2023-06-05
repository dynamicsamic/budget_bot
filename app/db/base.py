import datetime as dt
from functools import cache
from typing import Type

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm.attributes import QueryableAttribute

from app import settings


class ModelFieldsDetails:
    """Mixin that adds information about actual sqlalchemy table fields."""

    @classmethod
    @property
    def fields(cls) -> dict[str, Type[QueryableAttribute]]:
        return {
            attr_name: attr_obj
            for attr_name, attr_obj in cls.__dict__.items()
            if not attr_name.startswith("_")
            and hasattr(attr_obj, "primary_key")
        }

    @classmethod
    @property
    def fieldnames(cls) -> list[str]:
        return list(cls.fields.keys())

    @classmethod
    @property
    def fieldtypes(cls) -> list[str]:
        return [field.type for field in cls.fields.values()]

    @classmethod
    @property
    def primary_keys(cls) -> list[str]:
        return [
            fieldname
            for fieldname, field_obj in cls.fields.items()
            if getattr(field_obj, "primary_key")
        ]


class Base(DeclarativeBase):
    pass


class BaseModel(Base, ModelFieldsDetails):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.now(settings.TIME_ZONE)
    )
    last_updated: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=dt.datetime.now(settings.TIME_ZONE),
        onupdate=dt.datetime.now(settings.TIME_ZONE),
    )
