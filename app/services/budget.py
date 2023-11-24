from typing import Any

from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.sql._typing import _DMLColumnArgument

from app.db.models import Budget
from app.db.queries.crud import create, delete, get_all, update
from app.db.queries.extra import count


def get_user_budgets(
    db_session: Session | scoped_session, user_id: int
) -> Query[Budget]:
    return get_all(
        model=Budget,
        session=db_session,
        order_by=[-Budget.created_at, -Budget.id],
        filters=[Budget.user_id == user_id],
    )


def create_budget(
    db_session: Session | scoped_session,
    user_id: int,
    name: str,
    currency: str,
) -> Budget | None:
    return create(Budget, db_session, user_id=user_id, name=name, currency=currency)


def update_budget(
    db_session: Session | scoped_session,
    budget_id: int,
    update_kwargs: dict[_DMLColumnArgument, Any],
) -> bool:
    return update(Budget, db_session, budget_id, update_kwargs)


def delete_budget(
    db_session: Session | scoped_session,
    budget_id: int,
) -> bool:
    return delete(Budget, db_session, budget_id)


def count_user_budgets(
    db_session: Session | scoped_session, user_id: int
) -> Query[Budget]:
    return count(Budget, db_session, [Budget.user_id == user_id])
