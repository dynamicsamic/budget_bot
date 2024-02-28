import datetime as dt
import enum
from typing import Any, List, Optional, Type, TypeVar

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    InstrumentedAttribute,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.orm.attributes import QueryableAttribute

from app import settings
from app.utils import epoch_start, pretty_datetime

# any data type from sqlalchemy.sql.sqltypes
_SQLAlchemyDataType = TypeVar("_SQLAlchemyDataType")


class classproperty(property):
    # copied from https://stackoverflow.com/a/13624858
    def __get__(self, __instance: Any, __owner: type | None = None) -> Any:
        return self.fget(__owner)


class ModelFieldsDetails:
    """Mixin that adds information about actual sqlalchemy model fields."""

    @classproperty
    def fields(cls) -> dict[str, Type[QueryableAttribute]]:
        """Get actual model fields and their attribute classes."""
        return {
            attr_name: attr_class
            for attr_name, attr_class in cls.__dict__.items()
            if not attr_name.startswith("_")
            and getattr(attr_class, "is_attribute", None)
        }

    @classproperty
    def fieldnames(cls) -> set[str]:
        """Get actual model field names."""
        return set(cls.fields.keys())

    @classproperty
    def primary_keys(cls) -> set[str]:
        """Get actual model's primary keys."""
        return {
            fieldname
            for fieldname, field_obj in cls.fields.items()
            if getattr(field_obj, "primary_key", None)
        }

    @classmethod
    def get_tablename(cls) -> str:
        return cls.__tablename__.upper()


class Base(DeclarativeBase):
    pass


class AbstractBaseModel(Base, ModelFieldsDetails):
    """Parent class for all active models."""

    __abstract__ = True
    _public_name = ""

    id: Mapped[int] = mapped_column(primary_key=True, doc="id пользователя")
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

    def render(self) -> str:
        pass


class CategoryType(enum.Enum):
    EXPENSES = ("expenses", "Расходы")
    INCOME = ("income", "Доходы")

    def __init__(self, value, description) -> None:
        self._value_ = value
        self._description = description

    @property
    def description(self) -> str:
        return self._description


class User(AbstractBaseModel):
    __tablename__ = "user"
    _public_name = "Пользователь"

    tg_id: Mapped[int] = mapped_column(doc="Telegram id", unique=True)
    budget_currency: Mapped[str] = mapped_column(
        String(length=10),
        doc="Валюта",
        default="RUB",
    )
    is_active: Mapped[bool] = mapped_column(doc="Статус активен", default=True)
    categories: Mapped[List["Category"]] = relationship(
        back_populates="user",
        cascade="delete, merge, save-update",
        passive_deletes=True,
    )
    entries: Mapped[List["Entry"]] = relationship(
        back_populates="user",
        cascade="delete, merge, save-update",
        passive_deletes=True,
    )

    @classproperty
    def _datefield(cls) -> InstrumentedAttribute:
        return cls.created_at

    @classproperty
    def is_anonymous(cls):
        return False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, TelegramId={self.tg_id}, "
            f"Currency={self.budget_currency}, IsActive={self.is_active})"
        )

    def render(self) -> str:
        return f"Telegram id {self.tg_id}, валюта {self.budget_currency}"


class Category(AbstractBaseModel):
    __tablename__ = "entry_category"
    _public_name = "Категория"

    name: Mapped[str] = mapped_column(String(length=128), doc="Название")
    type: Mapped[Enum] = mapped_column(
        Enum(CategoryType, create_constraint=True), doc="Тип"
    )
    last_used: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        doc="Дата последнего применения",
        default=epoch_start(),
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), doc="id пользователя"
    )
    num_entries: Mapped[int] = mapped_column(
        doc="Количество транзакций", default=0
    )
    user: Mapped[User] = relationship(back_populates="categories")
    entries: Mapped[List["Entry"]] = relationship(back_populates="category")

    @classproperty
    def _datefield(cls) -> InstrumentedAttribute:
        return cls.last_used

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, "
            f"Name={self.name}, Type={self.type.value}, "
            f"UserId={self.user_id}, NumEntries={self.num_entries})"
        )

    def render(self) -> str:
        return (
            f"{self.name.capitalize()} ({self.type.description}), "
            f"{self.num_entries} {select_num_entries_ending(self.num_entries)}"
        )


class Entry(AbstractBaseModel):
    __tablename__ = "entry"
    _public_name = "Транзакция"

    # sum is an integer thus:
    # multiply float number by 100 before insert opeartions
    # and divide by 100 after select operations
    sum: Mapped[int] = mapped_column(
        Integer, CheckConstraint("sum != 0"), doc="Сумма"
    )
    description: Mapped[Optional[str]] = mapped_column(String, doc="Пояснение")
    transaction_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        doc="Дата транзакции",
        default=dt.datetime.now(settings.TIME_ZONE),
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), doc="id пользователя"
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("entry_category.id", ondelete="CASCADE"), doc="id категории"
    )
    user: Mapped[User] = relationship(back_populates="entries")
    category: Mapped["Category"] = relationship(back_populates="entries")

    @classproperty
    def _datefield(cls) -> InstrumentedAttribute:
        return cls.transaction_date

    @classproperty
    def _cashflowfield(cls) -> InstrumentedAttribute:
        return cls.sum

    @property
    def _sum(self) -> str:
        return f"{self.sum / 100:.2f}"

    @property
    def _transaction_date(self) -> str:
        return pretty_datetime(self.transaction_date)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, Sum={self._sum}, "
            f"Date={self._transaction_date}, CategoryId={self.category_id}, "
            f"UserId={self.user_id}, Description={self.description})"
        )

    def render(self) -> str:
        signed_sum = "+" + self._sum if self.sum > 0 else self._sum
        rendered = (
            f"{signed_sum} {self.user.budget_currency}, "
            f"{self.category.name}, {self._transaction_date}"
        )
        if self.description:
            rendered += f", {self.description}"

        return rendered


def select_num_entries_ending(num_entries: int) -> str:
    if num_entries == 1:
        return "операция"
    elif 1 < num_entries < 5:
        return "операции"
    return "операций"
