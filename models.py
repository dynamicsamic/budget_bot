import datetime as dt

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class NotNullColumn(Column):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("nullable", False)
        return super().__init__(*args, **kwargs)


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime(timezone=True), default=dt.datetime.now())
    last_updated = Column(
        DateTime(timezone=True),
        default=dt.datetime.now(),
        onupdate=dt.datetime.now(),
    )


class User(BaseModel):
    __tablename__ = "user"

    tg_username = NotNullColumn(String(length=256), unique=True)
    tg_id = NotNullColumn(Integer, unique=True)
    budget = relationship("Budget", back_populates="user")


class Budget:
    __tablename__ = "budget"

    name = NotNullColumn(String(length=256), unique=True)
    currency = Column(String(length=10), default="RUB")
    user_id = NotNullColumn(Integer, ForeignKey("user"))
    user = relationship("User", back_populates="budget")
    entries = relationship("Entry", back_populates="budget")


class Category:
    __tablename__ = "category"

    name = NotNullColumn(String(length=128))
    entries = relationship("Entry", back_populates="category")


class Entry:
    __tablename = "entry"

    budget_id = NotNullColumn(Integer, ForeignKey("budget"))
    budget = relationship("Budget", back_populates="entries")
    category_id = NotNullColumn(Integer, ForeignKey("category"))
    category = relationship("Category", back_populates="entries")
    sum = NotNullColumn(Integer)


"""
user.create(tg_id, tg_username)
budget.create(name, user)
entry.create(budget, category, sum)
/new_entry
enter sum
enter category

"""
