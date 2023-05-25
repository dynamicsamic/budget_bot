import datetime as dt
import enum
from typing import List, Optional, Self

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    select,
)
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
)

from app import settings


class Base(DeclarativeBase):
    pass


class Currency(enum.Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class BaseModel(Base):
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

    @classmethod
    def all(
        cls, session: Session, to_list: bool = False
    ) -> ScalarResult[Self] | list[Self]:
        """Return all instances either in list or in ScalarResult."""
        qs = session.scalars(select(cls))
        return qs.all() if to_list else qs

    @classmethod
    def count(cls, session: Session) -> int:
        """Return number of all instances in the DB."""
        query = select(func.count(cls.id))
        return session.scalar(query)


class User(BaseModel):
    __tablename__ = "user"

    tg_id: Mapped[int] = mapped_column(unique=True)
    tg_username: Mapped[str] = mapped_column(String(length=256), unique=True)
    budgets: Mapped[List["Budget"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id} "
            f"TelegramName={self.tg_username}, TelegramId={self.tg_id})"
        )


class Budget(BaseModel):
    __tablename__ = "budget"

    name: Mapped[str] = mapped_column(String(length=256), unique=True)
    currency: Mapped[Currency] = mapped_column(default=Currency.RUB)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="budgets")
    entries: Mapped[List["Entry"]] = relationship(
        back_populates="budget",
        cascade="all, delete",
    )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, UserId={self.user_id}, "
            f"Cur={self.currency.value}, Name={self.name})"
        )


class EntryCategory(BaseModel):
    __tablename__ = "entry_category"

    name: Mapped[str] = mapped_column(String(length=128), unique=True)
    entries: Mapped[List["Entry"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(Id={self.id}, Name={self.name})"


class Entry(BaseModel):
    __tablename__ = "entry"

    budget_id: Mapped[int] = mapped_column(ForeignKey("budget.id"))
    budget: Mapped["Budget"] = relationship(back_populates="entries")
    category_id: Mapped[int] = mapped_column(ForeignKey("entry_category.id"))
    category: Mapped["EntryCategory"] = relationship(back_populates="entries")
    sum: Mapped[int] = mapped_column(Integer, CheckConstraint("sum != 0"))
    description: Mapped[Optional[str]]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(Id={self.id}, Sum={self.sum}, "
            f"CategoryId={self.category_id}, BudgetId={self.budget_id}), "
            f"Description={self.description}"
        )
