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


class EntryType(enum.Enum):
    EXPENSES = "expenses"
    INCOME = "income"


class User(AbstractBaseModel):
    __tablename__ = "user"

    tg_id: Mapped[int] = mapped_column(unique=True)
    budgets: Mapped[List["Budget"]] = relationship(
        back_populates="user",
        cascade="delete, merge, save-update",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, TelegramId={self.tg_id})"
        )


class Budget(AbstractBaseModel):
    __tablename__ = "budget"

    name: Mapped[str] = mapped_column(String(length=256), unique=True)
    currency: Mapped[str] = mapped_column(
        String(length=4),
        CheckConstraint("length(currency) > 2 AND length(currency) < 5"),
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

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, UserId={self.user_id}, "
            f"Currency={self.currency}, Name={self.name})"
        )


class EntryCategory(AbstractBaseModel):
    __tablename__ = "entry_category"

    name: Mapped[str] = mapped_column(String(length=128), unique=True)
    type: Mapped[Enum] = mapped_column(Enum(EntryType, create_constraint=True))
    last_used: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime(year=1970, month=1, day=1)
    )
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budget.id", ondelete="CASCADE")
    )
    budget: Mapped["Budget"] = relationship(back_populates="categories")
    entries: Mapped[List["Entry"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, Name={self.name}, "
            f"Type={self.type.value}, BudgetId={self.budget_id})"
        )


class Entry(AbstractBaseModel):
    __tablename__ = "entry"

    # sum is an integer thus:
    # multiply float number by 100 before insert opeartions
    # and divide by 100 after select operations
    sum: Mapped[int] = mapped_column(Integer, CheckConstraint("sum != 0"))
    transaction_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.now(settings.TIME_ZONE)
    )
    description: Mapped[Optional[str]]
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budget.id", ondelete="CASCADE")
    )
    budget: Mapped["Budget"] = relationship(
        back_populates="entries", lazy="joined"
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("entry_category.id"))
    category: Mapped["EntryCategory"] = relationship(
        back_populates="entries", lazy="joined"
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
