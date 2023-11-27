from datetime import datetime
from typing import Any

from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.sql._typing import _DMLColumnArgument

from app.db.models import Entry
from app.db.queries.crud import create, delete, get_all, update
from app.db.queries.extra import count


def get_budget_entries(
    db_session: Session | scoped_session, budget_id: int
) -> Query[Entry]:
    return get_all(
        model=Entry,
        session=db_session,
        order_by=[Entry.transaction_date.desc(), Entry.id.desc()],
        filters=[Entry.budget_id == budget_id],
    )


def get_category_entries(
    db_session: Session | scoped_session, category_id: int
) -> Query[Entry]:
    return get_all(
        model=Entry,
        session=db_session,
        order_by=[Entry.transaction_date.desc(), Entry.id.desc()],
        filters=[Entry.category_id == category_id],
    )


def create_entry(
    db_session: Session | scoped_session,
    budget_id: int,
    category_id: int,
    sum: int,
    transaction_date: datetime = None,
    description: str = None,
) -> Entry | None:
    return create(
        Entry,
        db_session,
        budget_id=budget_id,
        category_id=category_id,
        sum=sum,
        transaction_date=transaction_date,
        description=description,
    )


def update_entry(
    db_session: Session | scoped_session,
    entry_id: int,
    update_kwargs: dict[_DMLColumnArgument, Any],
) -> bool:
    return update(Entry, db_session, entry_id, update_kwargs)


def delete_entry(
    db_session: Session | scoped_session,
    entry_id: int,
) -> bool:
    return delete(Entry, db_session, entry_id)


def count_budget_entries(
    db_session: Session | scoped_session, budget_id: int
) -> Query[Entry]:
    return count(Entry, db_session, [Entry.budget_id == budget_id])


def count_category_entries(
    db_session: Session | scoped_session, category_id: int
) -> Query[Entry]:
    return count(Entry, db_session, [Entry.category_id == category_id])
