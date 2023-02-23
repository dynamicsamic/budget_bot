import datetime as dt

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import declarative_base, relationship

import settings

Base = declarative_base()


class NotNullColumn(Column):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("nullable", False)
        super().__init__(*args, **kwargs)


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    created_at = Column(
        DateTime(timezone=True), default=dt.datetime.now(settings.TIME_ZONE)
    )
    last_updated = Column(
        DateTime(timezone=True),
        default=dt.datetime.now(settings.TIME_ZONE),
        onupdate=dt.datetime.now(settings.TIME_ZONE),
    )


class User(BaseModel):
    __tablename__ = "user"

    tg_username = NotNullColumn(String(length=256), unique=True)
    tg_id = NotNullColumn(Integer, unique=True)
    budget = relationship(
        "Budget",
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True,
    )

    def __str__(self):
        return f"{self.__class__.__name__}({self.tg_username}: {self.tg_id})"


class Budget(BaseModel):
    __tablename__ = "budget"

    name = NotNullColumn(String(length=256), unique=True)
    currency = Column(String(length=10), default="RUB")
    user_id = NotNullColumn(Integer, ForeignKey("user.id"))
    user = relationship("User", back_populates="budget")
    entries = relationship(
        "Entry",
        back_populates="budget",
        cascade="all, delete",
        passive_deletes=True,
    )


class Category(BaseModel):
    __tablename__ = "category"

    name = NotNullColumn(String(length=128))
    entries = relationship("Entry", back_populates="category")


class Entry(BaseModel):
    __tablename__ = "entry"

    budget_id = NotNullColumn(Integer, ForeignKey("budget.id"))
    budget = relationship("Budget", back_populates="entries")
    category_id = NotNullColumn(Integer, ForeignKey("category.id"))
    category = relationship("Category", back_populates="entries")
    sum = NotNullColumn(Numeric(2, 10))
    description = Column(String(length=256), nullable=True)


"""
user.create(tg_id, tg_username)
budget.create(name, user)
entry.create(budget, category, sum)
/new_entry
enter sum
enter category

"""
