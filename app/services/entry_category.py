from typing import Any

from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.sql._typing import _DMLColumnArgument

from app.db.models import EntryCategory, EntryType
from app.db.queries.crud import create, delete, get_all, update
from app.db.queries.extra import count


def get_budget_categories(
    db_session: Session | scoped_session, budget_id: int
) -> Query[EntryCategory]:
    return get_all(
        model=EntryCategory,
        session=db_session,
        order_by=[-EntryCategory.created_at, -EntryCategory.id],
        filters=[EntryCategory.budget_id == budget_id],
    )


def create_entry_category(
    db_session: Session | scoped_session,
    budget_id: int,
    name: str,
    type: EntryType,
) -> EntryCategory | None:
    return create(
        EntryCategory,
        db_session,
        budget_id=budget_id,
        name=name,
        type=type,
    )


def update_entry_category(
    db_session: Session | scoped_session,
    entry_category_id: int,
    update_kwargs: dict[_DMLColumnArgument, Any],
) -> bool:
    return update(EntryCategory, db_session, entry_category_id, update_kwargs)


def delete_entry_category(
    db_session: Session | scoped_session,
    entry_category_id: int,
) -> bool:
    return delete(EntryCategory, db_session, entry_category_id)


def count_budget_categories(
    db_session: Session | scoped_session, budget_id: int
) -> Query[EntryCategory]:
    return count(
        EntryCategory, db_session, [EntryCategory.budget_id == budget_id]
    )
