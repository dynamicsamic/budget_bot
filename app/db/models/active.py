import datetime as dt
import enum
from typing import Any, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Mapped,
    mapped_column,
    relationship,
)

from app import settings

from .base import AbstractBaseModel


class EntryType(enum.Enum):
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

    tg_id: Mapped[int] = mapped_column(unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    budgets: Mapped[List["Budget"]] = relationship(
        back_populates="user",
        cascade="delete, merge, save-update",
        passive_deletes=True,
    )

    @classmethod
    @property
    def _datefield(cls) -> InstrumentedAttribute:
        return cls.created_at

    @property
    def is_anonymous(self):
        return False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, "
            f"TelegramId={self.tg_id}, Active={self.is_active})"
        )


class Budget(AbstractBaseModel):
    __tablename__ = "budget"

    name: Mapped[str] = mapped_column(String(length=100), unique=True)
    currency: Mapped[str] = mapped_column(
        String(length=10),
        default="RUB",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship(back_populates="budgets")
    categories: Mapped[List["EntryCategory"]] = relationship(
        back_populates="budget",
        cascade="delete, merge, save-update",
        passive_deletes=True,
    )
    entries: Mapped[List["Entry"]] = relationship(
        back_populates="budget",
        cascade="delete, merge, save-update",
        passive_deletes=True,
    )
    num_categories: Mapped[int] = mapped_column(default=0)
    num_entries: Mapped[int] = mapped_column(default=0)

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.name = self._make_unique_name()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, UserId={self.user_id}, "
            f"Currency={self.currency}, Name={self.name})"
        )

    @classmethod
    @property
    def _datefield(cls) -> InstrumentedAttribute:
        return cls.created_at

    @property
    def public_name(self) -> str:
        *_, name = self.name.split(":")
        return name

    def render(self) -> str:
        return (
            f"{self.public_name}({self.currency.upper()}), "
            f"{self.num_entries} {select_num_entries_ending(self.num_entries)}"
        )

    def _make_unique_name(self) -> str:
        return f"user_{self.user_id}:{self.name}"


class EntryCategory(AbstractBaseModel):
    __tablename__ = "entry_category"

    name: Mapped[str] = mapped_column(String(length=128))
    type: Mapped[Enum] = mapped_column(Enum(EntryType, create_constraint=True))
    last_used: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime(year=1970, month=1, day=1)
    )
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budget.id", ondelete="CASCADE")
    )
    budget: Mapped["Budget"] = relationship(back_populates="categories")
    entries: Mapped[List["Entry"]] = relationship(back_populates="category")
    num_entries: Mapped[int] = mapped_column(default=0)

    @classmethod
    @property
    def _datefield(cls) -> InstrumentedAttribute:
        return cls.last_used

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, Name={self.name}, "
            f"Type={self.type.value}, BudgetId={self.budget_id})"
        )

    def render(self) -> str:
        return (
            f"{self.name} ({self.type.description}), "
            f"{self.num_entries} {select_num_entries_ending(self.num_entries)}"
        )


class Entry(AbstractBaseModel):
    __tablename__ = "entry"

    # sum is an integer thus:
    # multiply float number by 100 before insert opeartions
    # and divide by 100 after select operations
    sum: Mapped[int] = mapped_column(Integer, CheckConstraint("sum != 0"))
    description: Mapped[Optional[str]]
    transaction_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.now(settings.TIME_ZONE)
    )
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budget.id", ondelete="CASCADE")
    )
    budget: Mapped["Budget"] = relationship(back_populates="entries")
    category_id: Mapped[int] = mapped_column(ForeignKey("entry_category.id"))
    category: Mapped["EntryCategory"] = relationship(back_populates="entries")

    @classmethod
    @property
    def _datefield(cls) -> InstrumentedAttribute:
        return cls.transaction_date

    @classmethod
    @property
    def _cashflowfield(cls) -> InstrumentedAttribute:
        return cls.sum

    @property
    def _sum(self) -> str:
        return f"{self.sum / 100:.2f}"

    @property
    def _transaction_date(self) -> str:
        return f"{self.transaction_date:%Y-%m-%d %H:%M:%S}"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, Sum={self._sum}, "
            f"Date={self._transaction_date}, CategoryId={self.category_id}, "
            f"BudgetId={self.budget_id}, Description={self.description})"
        )

    def render(self) -> str:
        signed_sum = "+" + self._sum if self.sum > 0 else self._sum
        rendered = (
            f"{signed_sum} {self.budget.currency}, "
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
