import datetime as dt
from typing import Type

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm.attributes import QueryableAttribute

from app import settings
from app.utils import _SQLAlchemyDataType


class Base(DeclarativeBase):
    pass


class ModelFieldsDetails:
    """Mixin that adds information about actual sqlalchemy model fields."""

    @classmethod
    @property
    def fields(cls) -> dict[str, Type[QueryableAttribute]]:
        """Get actual model fields and their attribute classes."""
        return {
            attr_name: attr_obj
            for attr_name, attr_obj in cls.__dict__.items()
            if not attr_name.startswith("_")
            and getattr(attr_obj, "is_attribute", None)
        }

    @classmethod
    @property
    def fieldtypes(cls) -> dict[str, _SQLAlchemyDataType]:
        """Get actual model fields and their attribute sqlalchemy types."""
        return {
            attr_name: attr_obj.type
            for attr_name, attr_obj in cls.fields.items()
        }

    @classmethod
    @property
    def fieldnames(cls) -> set[str]:
        """Get actual model field names."""
        return set(cls.fields.keys())

    @classmethod
    @property
    def primary_keys(cls) -> set[str]:
        """Get actual model's primary keys."""
        return {
            fieldname
            for fieldname, field_obj in cls.fields.items()
            if getattr(field_obj, "primary_key")
        }


class AbstractBaseModel(Base, ModelFieldsDetails):
    """Parent class for all active models."""

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

    def __repr__(self) -> str:
        pass
