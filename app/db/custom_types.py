from typing import TypeVar

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import UnaryExpression

from .models.base import AbstractBaseModel

_OrderByValue = TypeVar(
    "_OrderByValue", InstrumentedAttribute, UnaryExpression
)
_BaseModel = TypeVar("_BaseModel", bound=AbstractBaseModel)
_ModelWithDatefield = TypeVar("_ModelWithDatefield", bound=AbstractBaseModel)
_ModelWithCashflowfield = TypeVar(
    "_ModelWithCashflowfield", bound=AbstractBaseModel
)
