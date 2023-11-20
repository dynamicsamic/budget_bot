import datetime as dt
import logging
from typing import Any, List, Literal, Optional, Sequence

from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql._typing import _DMLColumnArgument
from sqlalchemy.sql.elements import (
    ColumnElement,
    UnaryExpression,
)

from app.db.exceptions import InvalidFilter, InvalidOrderByValue
from app.db.models.base import AbstractBaseModel
from app.utils import DateGen, _ComparingExpression, _OrderByValue

from .utils import FilterExpression, check_iterable

logger = logging.getLogger(__name__)


DEFAULT_SESSION = None
DEFAULT_ORDER_BY = ("created_at", "id")
DEFAULT_FILTERS = None
DEFAULT_DATEFIELD = "created_at"
DEFAULT_CASHFLOWFIELD = "sum"


def create(
    model: AbstractBaseModel,
    session: Session | scoped_session,
    **create_kwargs: Any,
) -> AbstractBaseModel | None:
    """Create an instance of `self.model`.
    Args:
        kwargs: A mapping of `model's` attribute (field) names
        to their values.
    Returns:
        The newly created instance or None if error occured.
    """
    try:
        obj = model(**create_kwargs)
        session.add(obj)
        session.commit()
    except Exception as e:
        logger.error(f"Instance creation [FAILURE]: {e}")
        return
    logger.info(f"New instance of {model} created")
    return obj


def update(
    model: AbstractBaseModel,
    session: Session | scoped_session,
    id: int,
    update_kwargs: dict[_DMLColumnArgument, Any],
) -> bool:
    """Update `self.model` instance with given kwargs.
    Args:
        id_: Instance `id` field.
        kwargs: A mapping of `model's` attribute names (fields) that should be updated
        to new values.
    Returns:
        True if update performed successfully, False otherwise.
    """
    try:
        updated = bool(
            session.query(model).filter_by(id=id).update(update_kwargs)
        )
    except Exception as e:
        logger.error(
            f"{model.__tablename__.upper()} " f"instance update [FAILURE]: {e}"
        )
        return False
    if updated:
        session.commit()
        logger.info(
            f"{model.__tablename__.upper()} instance "
            f"with id `{id}` update [SUCCESS]"
        )
    else:
        logger.info(
            f"No instance of {model.__tablename__.upper()} "
            f"with id `{id}` found."
        )
    return updated


def delete(
    model: AbstractBaseModel,
    session: Session | scoped_session,
    id: int,
) -> bool:
    """Delete `self.model` instance with given id.

    Args:
        id_: Instance `id` field.
    Returns:
        True if delete performed successfully, False otherwise.
    """
    try:
        deleted = bool(session.query(model).filter_by(id=id).delete())
        session.commit()
    except SQLAlchemyError as e:
        logger.error(
            f"{model.__tablename__.upper()} " f"instance delete [FAILURE]: {e}"
        )
        return False
    if deleted:
        logger.info(
            f"{model.__tablename__.upper()} instance "
            f"with id `{id}` delete [SUCCESS]"
        )
    else:
        logger.warning(
            f"Attempt to delete instance of "
            f"{model.__tablename__.upper()} with id `{id}`. "
            "No delete performed."
        )
    return deleted


def get(
    model: AbstractBaseModel,
    session: Session | scoped_session,
    id: int,
):
    return _fetch(model, session, filters=[f"id=={id}"]).one_or_none()


def count(
    model: AbstractBaseModel,
    session: Session | scoped_session,
    filters: Optional[Sequence[_ComparingExpression]] = None,
) -> int:
    return _fetch(model, session, filters=filters).count()


def _fetch(
    model: AbstractBaseModel,
    session: Session | scoped_session,
    order_by: List[_OrderByValue] = DEFAULT_ORDER_BY,
    filters: Optional[Sequence[_ComparingExpression]] = None,
) -> Query[AbstractBaseModel]:
    """Basic SELECT query with ordering and optional filtering.
    This is the underlying query for almost all SELECT methods
    that are part of the public API of this class.
    Args:
        filters: Sequence of comparing expressions.
        reverse: Flag to reverse the order of resulting query.
    Returns:
        sqlalchemy.Query that contains selected `self.model` instances.
    """
    q = session.query(model).order_by(*_collect_order_by(model, order_by))

    if filters is not None:
        return q.filter(_collect_filters(model, filters))

    return q


def _collect_order_by(
    model: AbstractBaseModel, order_by: Sequence[_OrderByValue]
) -> List[InstrumentedAttribute | UnaryExpression]:
    """Construct a sequence of model attributes
    to be used in ORDER BY clause.

    Args:
        reverse: Flag to reverse the default ordering of fields.

    Returns:
        List of sqlalchemy model attributes.
    """
    order_by_ = []

    order_by_dict = _transform_to_order_by_dict(order_by)
    for attr, order in order_by_dict.items():
        field = getattr(model, attr)
        if order == "desc" and hasattr(field, "is_attribute"):
            field = field.desc()
        order_by_.append(field)
    return order_by_


def _transform_to_order_by_dict(
    order_by: Sequence[_OrderByValue],
) -> dict[_OrderByValue, Literal["asc", "desc"]]:
    order_by_dict = {}
    for attr in order_by:
        if not isinstance(attr, str):
            raise InvalidOrderByValue(
                f"`order_by` value must be a string, "
                f"not `{type(attr)}` type."
            )
        elif attr.startswith("-"):
            order_by_dict[attr[1:].strip()] = "desc"
        elif attr.endswith("-"):
            order_by_dict[attr[:-1].strip()] = "desc"
        else:
            order_by_dict[attr.strip()] = "asc"
    return order_by_dict


def _collect_filters(
    model, filters: Sequence[_ComparingExpression]
) -> ColumnElement[True]:
    """Convert filters into list of expressions for further processing.
    If any of expressions in filters is invalid,
    InvalidFilter will be raised
    Args:
        filters: A sequence of comparing expressions.
    Returns:
        List of built filter expressions.
    """
    check_iterable(filters, InvalidFilter)
    filter_expression = [
        FilterExpression(expression, model).build() for expression in filters
    ]
    return and_(True, *filter_expression)


def _between(
    model: AbstractBaseModel,
    session: Session | scoped_session,
    start: dt.datetime | dt.date,
    end: dt.datetime | dt.date,
    datefield: str = DEFAULT_DATEFIELD,
    order_by=DEFAULT_ORDER_BY,
    filters: Optional[Sequence[_ComparingExpression]] = None,
) -> Query[AbstractBaseModel]:
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
    date_column: InstrumentedAttribute = getattr(model, datefield)
    return _fetch(model, session, order_by, filters).filter(
        date_column.between(start, end)
    )


def today(
    model,
    session,
    date_info: DateGen,
    datefield: str = DEFAULT_DATEFIELD,
    order_by=DEFAULT_ORDER_BY,
    filters: Optional[Sequence[_ComparingExpression]] = None,
) -> Query[AbstractBaseModel]:
    """Fetch model instances between the start and end of today.
    Args:
        date_info: Instance of DateGen class.
        filters: Sequence of comparing expressions.
        reverse: Flag to reverse the order of resulting query.
    Returns:
        sqlclahemy.Query that contains model instances between given gaps.
    """
    start, end = date_info.date_range
    return _between(model, session, start, end, datefield, order_by, filters)
