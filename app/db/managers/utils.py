import operator as operators
import re
from typing import Any, Callable, Iterable, Literal, Sequence

from sqlalchemy.sql.expression import ColumnOperators

from app.db.exceptions import InvalidFilter, InvalidOrderByValue

# from . import BaseModelManager


class ManagerFieldDescriptor:
    def __init__(self, *, default, validators: Iterable[Callable] = None):
        self._default = default
        self._validators = validators

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, obj, type):
        if obj is None:
            return self._default

        return getattr(obj, self._name, self._default)

    def __set__(self, obj, value):
        for validator in self._validators:
            validator(obj, value)
        setattr(obj, self._name, value)


def check_iterable(obj: Any, exception: Exception):
    if not hasattr(obj, "__iter__"):
        raise exception(f"{obj} must be a sequence, not a {type(obj)}")


def transform_to_order_by_dict(
    order_by: Sequence[str],
) -> dict[str, Literal["asc", "desc"]]:
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
