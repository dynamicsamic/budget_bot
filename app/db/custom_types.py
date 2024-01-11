from dataclasses import dataclass
from typing import Any, Generator, Tuple, TypeVar

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import UnaryExpression

from .models import AbstractBaseModel

_OrderByValue = TypeVar(
    "_OrderByValue", InstrumentedAttribute, UnaryExpression
)
_BaseModel = TypeVar("_BaseModel", bound=AbstractBaseModel)
_ModelWithDatefield = TypeVar("_ModelWithDatefield", bound=AbstractBaseModel)
_ModelWithCashflowfield = TypeVar(
    "_ModelWithCashflowfield", bound=AbstractBaseModel
)


@dataclass
class GenericResult:
    result: Any

    def astuple(self) -> Tuple[Any]:
        return tuple(self.__dict__.values())

    def asdict(self) -> dict[str, Any]:
        return self.__dict__


@dataclass
class ErrorAttachedResult(GenericResult):
    error: Exception | None


@dataclass
class ModelCreateResult(ErrorAttachedResult):
    result: _BaseModel | None


@dataclass
class ModelUpdateDeleteResult(ErrorAttachedResult):
    result: bool | None


@dataclass
class ModelValidationResult(ErrorAttachedResult):
    result: bool


@dataclass
class GeneratorResult(GenericResult):
    result: Generator[_BaseModel, _BaseModel, None] | None
    is_empty: bool
    head: _BaseModel | None
