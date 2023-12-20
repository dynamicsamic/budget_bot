import datetime as dt
import logging
from typing import Any, List, Optional, Type

from sqlalchemy import and_
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Query,
    Session,
    scoped_session,
)
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.functions import GenericFunction

from app.db.custom_types import _BaseModel, _ModelWithDatefield, _OrderByValue

logger = logging.getLogger(__name__)


def fetch(
    model: Type[_BaseModel],
    session: Session | scoped_session,
    *,
    order_by: Optional[List[_OrderByValue]] = None,
    filters: Optional[List[BinaryExpression]] = None,
) -> Query[_BaseModel]:
    """Basic SELECT query with optional ordering and filtering.

    This is the underlying query for almost all SELECT functions
    that are part of this package's public API.

    Args:
        model: A subclass of app.models.base.AbstractBaseModel.
        session: An instance of sqlalchemy.orm.Session or scoped_session.
        order_by: A list model attributes or unary expressions on it.
        filters: A list of binary expressions on model attributes.

    Returns:
        sqlalchemy.Query that will produce a list of selected model objects
            when invoking the all() method.

    Examples:
        ```
        _fetch(Entry, db_session)
        ```
        produces SELECT * FROM entry

        ```
        _fetch(Entry, db_session, order_by=[-Entry.id], filters=[Entry.sum > 0])
        ```
        produces SELECT ... FROM entry WHERE entry.sum > 0 ORDER BY -entry.id
    """
    query = session.query(model)

    if order_by is not None:
        query = query.order_by(*order_by)

    if filters is not None:
        query = query.filter(and_(True, *filters))

    return query


def aggregate_fetch(
    session: Session | scoped_session,
    aggregate_function: GenericFunction,
    target_column: InstrumentedAttribute,
    filters: Optional[List[BinaryExpression]] = None,
) -> Any:
    query = session.query(aggregate_function(target_column))

    if filters is not None:
        query = query.filter(and_(True, *filters))

    return query.scalar()


def between(
    model: Type[_ModelWithDatefield],
    session: Session | scoped_session,
    start: dt.datetime | dt.date,
    end: dt.datetime | dt.date,
    order_by: Optional[List[_OrderByValue]] = None,
    filters: Optional[List[BinaryExpression]] = None,
) -> Query[_ModelWithDatefield]:
    """Fetch `model` instances between given borders.

    This is the underlying method for all public date range methods.

    Args:
        start: The start of a datetime (date) range.
        end: The end of a datetime (date) range.
        filters: Sequence of comparing expressions.
        reverse: Flag to reverse the order of resulting query.

    Returns:
        sqlclahemy.Query that contains model instances between given gaps.
    """
    filters = filters or []
    filters.append(model._datefield.between(start, end))
    return fetch(model, session, order_by=order_by, filters=filters)


def aggregate_between(
    model: Type[_ModelWithDatefield],
    session: Session | scoped_session,
    start: dt.datetime | dt.date,
    end: dt.datetime | dt.date,
    aggregate_function: GenericFunction,
    target_column: InstrumentedAttribute,
    filters: Optional[List[BinaryExpression]] = None,
) -> Query[_ModelWithDatefield]:
    """Fetch `model` instances between given borders.

    This is the underlying method for all public date range methods.

    Args:
        start: The start of a datetime (date) range.
        end: The end of a datetime (date) range.
        filters: Sequence of comparing expressions.
        reverse: Flag to reverse the order of resulting query.

    Returns:
        sqlclahemy.Query that contains model instances between given gaps.
    """
    filters = filters or []
    filters.append(model._datefield.between(start, end))
    return aggregate_fetch(
        session, aggregate_function, target_column, filters=filters
    )
