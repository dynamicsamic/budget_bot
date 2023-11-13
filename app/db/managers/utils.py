import operator as operators
import re
from typing import Any, Callable, Iterable, Literal, Sequence, Type, TypeVar

from sqlalchemy import func as sql_func
from sqlalchemy.orm import InstrumentedAttribute, Query
from sqlalchemy.sql.elements import BinaryExpression

from app.db.exceptions import (
    BudgetBotDataBaseException,
    ImproperlyConfigured,
    InvalidFilter,
    InvalidOrderByValue,
    InvalidSumField,
)
from app.db.models.base import AbstractBaseModel

from . import core

# strings like: "id>1", "created_at == 12.01.2020", "sum<10000" etc.
_ComparingExpression = TypeVar("_ComparingExpression", bound=str)

# string like: "-id", "created_at", "sum-" etc.
_OrderByValue = TypeVar("_OrderByValue", bound=str)


class ManagerFieldDescriptor:
    def __init__(
        self,
        *,
        default,
        validators: Iterable[
            Callable[["core.BaseModelManager", Any], None]
        ] = tuple(),
    ):
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


def transform_to_order_by_dict(
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


class SumExtendedQuery:
    def __init__(
        self, model: AbstractBaseModel, sum_field__: str, query: Query
    ) -> None:
        sum_field = getattr(model, sum_field__, None)

        if not sum_field:
            raise InvalidSumField(
                f"Model {model} does not have {sum_field__} attribute."
            )

        self.model = model
        self.sum_field = sum_field
        self.query = query

    def income(self) -> Query:
        q = self.query.filter(self.sum_field > 0)
        setattr(q, "sum", lambda: self._sum(q))
        return q

    def expenses(self) -> Query:
        q = self.query.filter(self.sum_field < 0)
        setattr(q, "sum", lambda: self._sum(q))
        return q

    def total_sum(self) -> int:
        return self._sum(self.query)

    def _sum(self, q: Query) -> int:
        return q.with_entities(sql_func.sum(self.sum_field)).scalar() or 0


class FilterExpression:
    valid_operators = {
        ">": "gt",
        ">=": "ge",
        "<": "lt",
        "<=": "le",
        "==": "eq",
        "!=": "ne",
    }

    def __init__(
        self, expression: _ComparingExpression, model: Type[AbstractBaseModel]
    ) -> None:
        try:
            attr_name, sign, value = re.split("([<>!=]+)", expression)
        except ValueError:
            raise InvalidFilter(
                """Filter should follow pattern:
                      <model_attribute><compare_operator><value>.
                      Example: `sum>1`, `id == 2`"""
            )

        self.model = model
        self._attr_name: str = attr_name.strip()
        self._sign: str = sign
        self._value: str = value.strip()

        self._operator: Callable | None = None
        self._attr: InstrumentedAttribute | None = None

    def validate(self):
        if not self._value or not self._attr_name:
            raise InvalidFilter(
                "Filter must contain a model attribute name and a value."
            )

        operator = getattr(
            operators, self.valid_operators.get(self._sign, "None"), None
        )
        attr = getattr(self.model, self._attr_name, None)

        if operator is None:
            raise InvalidFilter(f"Invalid comparing sign: `{self._sign}`")

        if attr is None:
            raise InvalidFilter(
                f"""Model `{self.model}` 
                   does not have `{self._attr_name}` attribute."""
            )

        self._operator = operator
        self._attr = attr

    @property
    def is_valid(self):
        try:
            self.validate()
        except BudgetBotDataBaseException:
            return False
        return True

    def build(self) -> BinaryExpression:
        if self.is_valid:
            return self._operator(self._attr, self._value)
        else:
            raise ImproperlyConfigured(
                "Cannot call `build` on invalid FilterExpression."
                "Run `self.validate` to check errors."
            )
