import operator as operators
import re
from typing import Any, Sequence

from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.sql.expression import ColumnOperators
from sqlalchemy.types import Date, DateTime, Float, Integer, Numeric

from app.db.exceptions import (
    InvalidCashflowield,
    InvalidDateField,
    InvalidDBSession,
    InvalidFilter,
    InvalidOrderByValue,
)

from .utils import transform_to_order_by_dict


def check_iterable(obj: Any, exception: Exception):
    if not hasattr(obj, "__iter__"):
        raise exception(f"{obj} must be a sequence, not a {type(obj)}")


def validate_db_session(manager, session: Any) -> None:
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


def validate_order_by(manager, order_by: Sequence[str]) -> None:
    check_iterable(order_by, InvalidOrderByValue)
    order_by_dict = transform_to_order_by_dict(order_by)
    if invalid_fields := set(order_by_dict.keys()) - manager.model.fieldnames:
        raise InvalidOrderByValue(
            f"""Following values can not be 
            used as `order_by` args: {', '.join(invalid_fields)}."""
        )


def validate_filters(
    manager,
    filters: Sequence[str] = None,
    return_filters: bool = False,
) -> list[ColumnOperators] | None:
    filters = filters or manager.filters
    validated = []

    if filters:
        check_iterable(filters, InvalidFilter)
        valid_signs = {
            ">": "gt",
            ">=": "ge",
            "<": "lt",
            "<=": "le",
            "==": "eq",
            "!=": "ne",
        }
        for filter in filters:
            try:
                attr_, sign, value = re.split("([<>!=]+)", filter)
            except ValueError:
                raise InvalidFilter(
                    """Filter should follow pattern:
                          <model_attribute><compare_operator><value>.
                          Example: `sum>1`, `id == 2`"""
                )

            attr = getattr(manager.model, attr_.strip(), None)
            operator = getattr(operators, valid_signs.get(sign, "None"), None)

            if attr is None:
                raise InvalidFilter(
                    f"""Model `{manager.model}` 
                        does not have `{attr_}` atribute."""
                )

            elif operator is None:
                raise InvalidFilter(f"Invalid comparing sign: `{sign}`")

            elif not value:
                raise InvalidFilter("Filter must have a value.")

            if return_filters:
                validated.append(operator(attr, value.strip()))

    if return_filters:
        return validated


def validate_datefield(self, datefield_: str):
    if datefield := getattr(self.model, datefield_, None):
        if not isinstance(datefield.type, (Date, DateTime)):
            raise InvalidDateField(
                "Datefield must be of sqlalchemy `Date` or `Datetime` types."
            )
    else:
        raise InvalidDateField(
            f"""Model `{self.model}`
                does not have `{datefield_}` atribute."""
        )


def validate_cashflowfield(manager, cf_field_name: str) -> None:
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
