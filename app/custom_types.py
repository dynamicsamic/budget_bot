from dataclasses import dataclass
from typing import Any, Generator, Tuple, TypedDict, TypeVar

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import UnaryExpression

from app.db.models import AbstractBaseModel

_OrderByValue = TypeVar(
    "_OrderByValue", InstrumentedAttribute, UnaryExpression
)
_BaseModel = TypeVar("_BaseModel", bound=AbstractBaseModel)
_ModelWithDatefield = TypeVar("_ModelWithDatefield", bound=AbstractBaseModel)
_ModelWithCashflowfield = TypeVar(
    "_ModelWithCashflowfield", bound=AbstractBaseModel
)


class _MatchFnReturnDict(TypedDict):
    context: dict[str, Any]
    err_msg: str | None


@dataclass
class GenericResult:
    result: Any

    def astuple(self) -> Tuple[Any]:
        return tuple(self.__dict__.values())

    def asdict(self) -> dict[str, Any]:
        return self.__dict__


@dataclass
class GeneratorResult(GenericResult):
    result: Generator[_BaseModel, _BaseModel, None] | None
    is_empty: bool
    head: _BaseModel | None
