from typing import Any, Sequence, Type

from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.types import Date, DateTime, Float, Integer, Numeric

from app.db.exceptions import (
    InvalidCashflowield,
    InvalidDateField,
    InvalidDBSession,
    InvalidFilter,
    InvalidOrderByValue,
)

from . import core
from .utils import (
    FilterExpression,
    _ComparingExpression,
    _OrderByValue,
    transform_to_order_by_dict,
)


def check_iterable(obj: Any, exception: Type[Exception]) -> None:
    """Check if given object is an iterable.

    Args:
        obj: Any Python object, that should be checked.
        exception: Any subclass of Python's Exception.
    Returns:
        None.
    Raises:
        Instance of provided exception.
    """
    if not hasattr(obj, "__iter__"):
        raise exception(f"{obj} must be a sequence, not a {type(obj)}")


def validate_db_session(_: "core.BaseModelManager", session: Any) -> None:
    """Check if given database session is a valid sqlalchemy session.

    Args:
        _: A placeholder for manager argument being passed by a caller.
            This serves only one purpose: be compatible with
            `ManagerFieldDescriptor` __set__ method.
        session: Any object that should be tested as valid sqlalchemy session.

    Returns:
        None.

    Raises:
        InvalidDBSession if given session is not instance of sqlalchemy session
        or if given session is not active.
    """

    if session is None:
        return

    if not isinstance(session, (Session, scoped_session)):
        raise InvalidDBSession(
            f"session must be an instance of either sqlalchemy.orm "
            f"Session or scoped_session, not `{type(session)}.` "
        )

    if not session.is_active:
        raise InvalidDBSession(
            "Inactive session detected! `session` must be active."
        )


def validate_order_by(
    manager: "core.BaseModelManager", order_by: Sequence[_OrderByValue]
) -> None:
    """Check if a sequence may serve as `BaseModelManager.order_by` argument.

    Args:
        manager: Instance of BaseModelManager.
        order_by: A sequence of order_by values.

    Returns:
        None.

    Raises:
        InvalidOrderByValue if any of order_by values is invalid.
    """
    check_iterable(order_by, InvalidOrderByValue)
    order_by_dict = transform_to_order_by_dict(order_by)
    if invalid_fields := set(order_by_dict.keys()) - manager.model.fieldnames:
        raise InvalidOrderByValue(
            f"""Following values can not be 
            used as `order_by` args: {', '.join(invalid_fields)}."""
        )


def validate_filters(
    manager: "core.BaseModelManager",
    filters: Sequence[_ComparingExpression],
) -> None:
    """Check if a sequence may serve as `BaseModelManager.filters` argument.

    Args:
        manager: Instance of BaseModelManager.
        filters: A sequence of comparing expressions.

    Returns:
        None.

    Raises:
        InvalidFilter if any of expressions in filters is invalid.
    """
    check_iterable(filters, InvalidFilter)

    for expression in filters:
        FilterExpression(expression, manager.model).validate()


def validate_datefield(manager: "core.DateRangeQueryManager", datefield_: str):
    """Check if a value may serve as
    `DateRangeQueryManager.datefield` argument.

    Args:
        manager: Instance of DateRangeQueryManager.
        datefield_: Fieldname that should be tested as valid datefield.

    Returns:
        None.

    Raises:
        InvalidDateField if either manager's model doesn't have a field
        with such name or if it's not a date or datetime field.
    """
    if datefield := getattr(manager.model, datefield_, None):
        if not isinstance(datefield.type, (Date, DateTime)):
            raise InvalidDateField(
                "Datefield must be of sqlalchemy `Date` or `Datetime` types."
            )
    else:
        raise InvalidDateField(
            f"""Model `{manager.model}`
                does not have `{datefield_}` atribute."""
        )


def validate_cashflowfield(
    manager: "core.CashFlowQueryManager", cf_field_name: str
) -> None:
    """Check if a value may serve as
    `CashFlowQueryManager.cashflowfield` argument.

    Args:
        manager: Instance of CashFlowQueryManager.
        cf_field_name: Fieldname that should be tested as valid cashflowfield.

    Returns:
        None.

    Raises:
        InvalidCashflowield if either manager's model doesn't have a field
        with such name or if it is not a numeric field.
    """
    if cashflowfield := getattr(manager.model, cf_field_name, None):
        if not isinstance(
            cashflowfield.type, (Integer, Float, Numeric)
        ) or not issubclass(
            cashflowfield.type.__class__, (Integer, Float, Numeric)
        ):
            raise InvalidCashflowield(
                "Cashflowfield must be of sqlalchemy `Integer`, "
                "`Float` or `Numeric` types or its subclasses."
            )
    else:
        raise InvalidCashflowield(
            f"Model `{manager.model}`"
            f"does not have `{cf_field_name}` atribute."
        )
