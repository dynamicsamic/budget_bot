from typing import Any, Callable, Iterable, Literal, Sequence

from sqlalchemy import func as sql_func
from sqlalchemy.orm import Query

from app.db.exceptions import InvalidOrderByValue, InvalidSumField
from app.db.models.base import AbstractBaseModel

from . import BaseModelManager


class ManagerFieldDescriptor:
    def __init__(
        self,
        *,
        default,
        validators: Iterable[
            Callable[[BaseModelManager, Any], None]
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
