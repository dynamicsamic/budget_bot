import datetime as dt
import enum
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import settings

from .base import AbstractBaseModel


class Currency(enum.Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class EntryType(enum.Enum):
    EXPENSES = "expenses"
    INCOME = "income"


class User(AbstractBaseModel):
    __tablename__ = "user"

    tg_id: Mapped[int] = mapped_column(unique=True)
    tg_username: Mapped[str] = mapped_column(String(length=256), unique=True)
    budgets: Mapped[List["Budget"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, "
            f"TelegramName={self.tg_username}, TelegramId={self.tg_id})"
        )


class Budget(AbstractBaseModel):
    __tablename__ = "budget"

    name: Mapped[str] = mapped_column(String(length=256), unique=True)
    currency: Mapped[Enum] = mapped_column(
        Enum(Currency, create_constraint=True), default=Currency.RUB
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship(
        back_populates="budgets", lazy="joined"
    )
    entries: Mapped[List["Entry"]] = relationship(
        back_populates="budget",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, UserId={self.user_id}, "
            f"Cur={self.currency.value}, Name={self.name})"
        )


class EntryCategory(AbstractBaseModel):
    __tablename__ = "entry_category"

    name: Mapped[str] = mapped_column(String(length=128), unique=True)
    type: Mapped[Enum] = mapped_column(Enum(EntryType, create_constraint=True))
    last_used: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime(year=1970, month=1, day=1)
    )
    entries: Mapped[List["Entry"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, "
            f"Name={self.name}, Type={self.type.value})"
        )


class Entry(AbstractBaseModel):
    __tablename__ = "entry"

    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budget.id", ondelete="CASCADE")
    )
    budget: Mapped["Budget"] = relationship(back_populates="entries")
    category_id: Mapped[int] = mapped_column(ForeignKey("entry_category.id"))
    category: Mapped["EntryCategory"] = relationship(back_populates="entries")

    # sum is an integer thus:
    # multiply float number by 100 before insert opeartions
    # and divide by 100 after select operations
    sum: Mapped[int] = mapped_column(Integer, CheckConstraint("sum != 0"))
    description: Mapped[Optional[str]]
    transaction_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.now(settings.TIME_ZONE)
    )

    @property
    def _sum(self) -> str:
        return f"{self.sum / 100:.2f}"

    def __repr__(self) -> str:
        trunc_date = f"{self.transaction_date:%Y-%m-%d %H:%M:%S}"
        return (
            f"{self.__class__.__name__}(Id={self.id}, Sum={self._sum}, "
            f"Date={trunc_date}, CategoryId={self.category_id}, "
            f"BudgetId={self.budget_id}, Description={self.description})"
        )
