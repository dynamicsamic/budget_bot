import datetime as dt
import logging
from dataclasses import dataclass
from types import MethodType
from typing import Any, Callable, List, Literal, Sequence, Type

from sqlalchemy import Date, DateTime, and_
from sqlalchemy import func as sql_func
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, joinedload, scoped_session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement, UnaryExpression
from sqlalchemy.types import Float, Integer, Numeric

from app.db.exceptions import (
    InvalidCashflowield,
    InvalidDateField,
    InvalidOrderByValue,
    InvalidSumField,
)
from app.db.models import Budget, Entry, EntryCategory, User
from app.db.models.base import AbstractBaseModel
from app.utils import DateGen

from .utils import (
    ManagerFieldDescriptor,
    transform_to_order_by_dict,
    validate_filters,
    validate_order_by,
)

logger = logging.getLogger(__name__)

DEFAULT_ORDER_BY = ("created_at", "id")
DEFAULT_FILTERS = None
DEFAULT_DATEFIELD = "created_at"
DEFAULT_CASHFLOWFIELD = "sum"


@dataclass
class BaseModelManager:
    """Interface for performig basic operations with data."""

    __short_name__ = "base"

    model: Type[AbstractBaseModel]
    session: Session | scoped_session = None
    order_by: Sequence[str] = ManagerFieldDescriptor(
        default=DEFAULT_ORDER_BY, validators=[validate_order_by]
    )
    filters: Sequence[str] = ManagerFieldDescriptor(
        default=DEFAULT_FILTERS, validators=[validate_filters]
    )  #  like ["id>2", "sum == 1"]

    def __call__(self, session: Session | scoped_session) -> None:
        """Allow `session` be associated
        with manager after it's creation.

        #### Example:
        create manger and leave it for later use
        `manager = BaseManager(BaseModel)`

        when you obtain session (e.g. via middleware)
        associate it with manager
        `manager(request.session)`
        `manager.some_method()`
        """
        if (
            isinstance(session, (Session, scoped_session))
            and session.is_active
        ):
            self.session = session
            return self

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(model={self.model.__tablename__}, "
            f"session={self.session}, order_by={self.order_by}, "
            f"filters={self.filters})"
        )

    def create(self, **kwargs) -> AbstractBaseModel | None:
        """Create an instance of `self.model`.
        Return created instance in case of success.
        Return `None` in case of failure.
        """
        try:
            obj = self.model(**kwargs)
            self.session.add(obj)
            self.session.commit()
        except Exception as e:
            logger.error(f"Instance creation [FAILURE]: {e}")
            return

        logger.info(f"New instance of {self.model} created")
        return obj

    def update(
        self,
        id_: int,
        **kwargs,
    ) -> bool:
        """Update `self.model` object."""
        try:
            updated = bool(
                self.session.query(self.model).filter_by(id=id_).update(kwargs)
            )
        except Exception as e:
            logger.error(
                f"{self.model.__tablename__.upper()} "
                f"instance update [FAILURE]: {e}"
            )
            return False

        if updated:
            self.session.commit()
            logger.info(
                f"{self.model.__tablename__.upper()} instance "
                f"with id `{id_}` update [SUCCESS]"
            )
        else:
            logger.info(
                f"No instance of {self.model.__tablename__.upper()} "
                f"with id `{id_}` found."
            )
        return updated

    def delete(self, id_: int) -> bool:
        """Delete `self.model` object with given id."""
        try:
            deleted = bool(
                self.session.query(self.model).filter_by(id=id_).delete()
            )
            self.session.commit()
        except SQLAlchemyError as e:
            logger.error(
                f"{self.model.__tablename__.upper()} "
                f"instance delete [FAILURE]: {e}"
            )
            return False
        if deleted:
            logger.info(
                f"{self.model.__tablename__.upper()} instance "
                f"with id `{id_}` delete [SUCCESS]"
            )
        else:
            logger.warning(
                f"Attempt to delete instance of "
                f"{self.model.__tablename__.upper()} with id `{id_}`. "
                "No delete performed."
            )
        return deleted

    def get(self, id_: int) -> AbstractBaseModel | None:
        """Retrieve `self.model` object."""
        return self.session.get(self.model, id_)

    def get_by(self, **kwargs) -> AbstractBaseModel | None:
        """Retrieve `self.model` object filtered by kwargs."""
        if valid_kwargs := self._clean_kwargs(kwargs):
            return (
                self.session.query(self.model)
                .filter_by(**valid_kwargs)
                .first()
            )

    def all(self, reverse: bool = False) -> Query[AbstractBaseModel]:
        """Retrieve all `self.model` objets."""
        return self._fetch(reverse=reverse)

    def list(self, reverse: bool = False) -> List[AbstractBaseModel]:
        """Retrieve all `self.model` objets in list."""
        return self._fetch(reverse=reverse).all()

    def select(
        self,
        *,
        filters: Sequence[str],
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        return self._fetch(filters, reverse)

    def count(self) -> int:
        """Calculate number of all `self.model` objects."""
        return self.session.query(self.model.id).count()

    def exists(self, id_: int = None, **kwargs) -> bool:
        """Tell wether `self.model` object with given id exists or not."""
        if id_:
            kwargs["id"] = id_

        if not kwargs:
            return False

        try:
            return bool(
                self.session.scalar(select(self.model.id).filter_by(**kwargs))
            )
        except Exception:
            return False

    def first(
        self, *, filters: Sequence[str] = None
    ) -> AbstractBaseModel | None:
        """Retrieve first `model` instance in ascending query."""
        return self.first_n(1, filters=filters).one_or_none()

    def last(
        self, *, filters: Sequence[str] = None
    ) -> AbstractBaseModel | None:
        """Retrieve last `model` instance in discending query."""
        return self.last_n(1, filters=filters).one_or_none()

    def first_n(
        self, n: int, *, filters: Sequence[str] = None
    ) -> Query[AbstractBaseModel]:
        """Retrieve specific number of `model` instances
        sorted in ascending order.
        """
        return self._fetch_n(n, filters)

    def last_n(
        self, n: int, *, filters: Sequence[str] = None
    ) -> Query[AbstractBaseModel]:
        """Retrieve specific number of `model` instances
        sorted in descending order.
        """
        return self._fetch_n(n, filters, True)

    def _clean_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        return {
            fieldname: value
            for fieldname, value in kwargs.items()
            if fieldname in self.model.fieldnames
        }

    def _fetch_n(
        self, n: int, filters: Sequence[str] = None, reverse: bool = False
    ) -> Query[AbstractBaseModel]:
        return self._fetch(filters, reverse).limit(n)

    def _fetch(
        self, filters: Sequence[str] = None, reverse: bool = False
    ) -> Query[AbstractBaseModel]:
        q = self.session.query(self.model).order_by(
            *self._compile_order_by(reverse)
        )
        filter_by = self._compile_filter_expr(filters)
        if filter_by is not None:
            return q.filter(filter_by)

        return q

    def _compile_order_by(
        self, reverse: bool
    ) -> List[InstrumentedAttribute | UnaryExpression]:
        order_by_ = []
        order_by_dict = (
            self._reversed_order_by_dict if reverse else self._order_by_dict
        )
        for attr, order in order_by_dict.items():
            field = getattr(self.model, attr)
            if order == "desc" and hasattr(field, "is_attribute"):
                field = field.desc()
            order_by_.append(field)
        return order_by_

    def _compile_filter_expr(
        self, filters: Sequence[str] = None
    ) -> ColumnElement[True] | None:
        filters = filters or self.filters

        if not filters:
            return

        return and_(
            True, *validate_filters(self, filters, return_filters=True)
        )

    @property
    def _order_by_dict(self) -> dict[str, Literal["asc", "desc"]]:
        return transform_to_order_by_dict(self.order_by)

    @property
    def _reversed_order_by_dict(self) -> dict[str, Literal["asc", "desc"]]:
        return {
            attr: "desc" if order == "asc" else "asc"
            for attr, order in self._order_by_dict.items()
        }

    def _set_default_order_by(self):
        self._order_by = DEFAULT_ORDER_BY

    def _reset_filters(self):
        self._filters = DEFAULT_FILTERS


@dataclass
class DateQueryModelManager(BaseModelManager):
    """
    BaseModelManager extended with methods for
    making queries with datetime gaps.
    """

    __short_name__ = "date"

    _datefield: str = DEFAULT_DATEFIELD

    def __post_init__(self) -> None:
        super().__post_init__()
        self._validate_datefield(self._datefield)

    def __repr__(self) -> str:
        text = super().__repr__()
        return f"{text[:-1]}, datefield='{self.datefield}')"

    @property
    def datefield(self) -> str:
        return self._datefield

    @datefield.setter
    def datefield(self, datefield_: str) -> None:
        self._validate_datefield(datefield_)
        self._datefield = datefield_

    def today(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        return self._between(*date_info.date_range, filters, reverse)

    def yesterday(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        return self._between(*date_info.yesterday_range, filters, reverse)

    def this_week(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        return self._between(*date_info.week_range, filters, reverse)

    def this_month(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        return self._between(*date_info.month_range, filters, reverse)

    def this_year(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        return self._between(*date_info.year_range, filters, reverse)

    def _between(
        self,
        start: dt.datetime | dt.date,
        end: dt.datetime | dt.date,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Fetch all instances of `model` filtered
        between given borders.
        """
        date_column = getattr(self.model, self.datefield)
        return self._fetch(filters, reverse).filter(
            date_column.between(start, end)
        )

    def _validate_datefield(self, datefield_: str):
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

    def _set_default_datefield(self):
        self._datefield = DEFAULT_DATEFIELD


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


@dataclass
class CashFlowQueryManager(DateQueryModelManager):
    __short_name__ = "cashflow"

    _cashflowfield: str = DEFAULT_CASHFLOWFIELD

    def __post_init__(self) -> None:
        super().__post_init__()
        self._validate_cashflowfield(self._cashflowfield)

    def __repr__(self) -> str:
        text = super().__repr__()
        return f"{text[:-1]}, cashflowfield='{self.cashflowfield}')"

    def __getattribute__(self, __name: str) -> Any:
        """Decorate methods that return `Query` with
        `self._extend_query` decorator.
        """
        attr = super().__getattribute__(__name)

        if callable(attr):
            return_type = attr.__annotations__.get("return")
            if return_type is Query:
                try:
                    return self._extend_query(attr)
                except Exception:
                    return attr
        return attr

    @property
    def cashflowfield(self) -> str:
        return self._cashflowfield

    @cashflowfield.setter
    def cashflowfield(self, cashflowfield_: str) -> None:
        self._validate_cashflowfield(cashflowfield_)
        self._cashflowfield = cashflowfield_

    def _extend_query(self, f: Callable[..., Query]) -> Query:
        """Add `ExtendedQuery` methods as `ext` attribute
        to a query.
        """

        def inner(*args, **kwargs):
            query = f(*args, **kwargs)
            setattr(
                query,
                "ext",
                SumExtendedQuery(self.model, self._cashflowfield, query),
            )
            return query

        return inner

    def _validate_cashflowfield(self, cf_field_name: str) -> None:
        if cashflowfield := getattr(self.model, cf_field_name, None):
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
                f"Model `{self.model}`"
                f"does not have `{cf_field_name}` atribute."
            )

    def _set_default_cashflowfield(self) -> None:
        self._cashflowfield = DEFAULT_CASHFLOWFIELD


def fetch_joined(
    self, filters: Sequence[str] = None, reverse: bool = False
) -> Query[AbstractBaseModel]:
    """Fetch budget and category data when querying entries."""
    q = super(self.__class__, self)._fetch(filters, reverse)
    return q.options(
        joinedload(self.model.budget, innerjoin=True),
        joinedload(self.model.category, innerjoin=True),
    )


def EntryManager(
    manager: Type[BaseModelManager],
    session: Session | scoped_session = None,
    order_by: Sequence[str] = DEFAULT_ORDER_BY,
    filters: Sequence[str] = DEFAULT_FILTERS,
    datefield: str = DEFAULT_DATEFIELD,
    cashflowfield: str = DEFAULT_CASHFLOWFIELD,
) -> BaseModelManager:
    if manager is BaseModelManager:
        manager = manager(Entry, session, order_by, filters)
    elif manager is DateQueryModelManager:
        manager = manager(Entry, session, order_by, filters, datefield)
    elif manager is CashFlowQueryManager:
        manager = manager(
            Entry, session, order_by, filters, datefield, cashflowfield
        )
    else:
        return

    manager._fetch = MethodType(fetch_joined, manager)
    return manager


class ModelManagerSet:
    def __init__(
        self,
        model: Type[AbstractBaseModel],
        **manager_init_kwargs: dict[str, Any],
    ) -> None:
        self.model = model
        self.manager_init_kwargs = manager_init_kwargs

    def __repr__(self) -> str:
        manager_methods = [
            name
            for name, attr in self.__dict__.items()
            if callable(attr) and not name.startswith("_") and name != "model"
        ]
        return (
            f"{self.__class__.__name__}(model={self.model.__tablename__}, "
            f"managers=[{', '.join(manager_methods)}])"
        )


@dataclass
class ModelManagerSetMethod:
    manager: Type[BaseModelManager]
    manager_set: ModelManagerSet

    def __call__(self, **manager_init_kwargs: dict[str, Any]):
        return self.manager(
            self.manager_set.model, **self.filter_kwargs(manager_init_kwargs)
        )

    def filter_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        manager_set_kwargs = self.manager_set.manager_init_kwargs or {}
        for attr, value in kwargs.items():
            if attr in self.manager_fields and value is not None:
                manager_set_kwargs.update({attr: value})
        return manager_set_kwargs

    @property
    def manager_fields(self) -> set[str]:
        valid_fields = set(self.manager.__match_args__)
        valid_fields.discard("model")
        return valid_fields


class ModelManagerFactory:
    def __init__(
        self,
        model: Type[AbstractBaseModel],
        managers: Sequence[Type[BaseModelManager]],
        **manager_init_kwargs: dict[str, Any],
    ) -> None:
        self.model = model
        self.managers = managers
        self.manager_init_kwargs = manager_init_kwargs

        self.manager_set = ModelManagerSet(model, **self.manager_init_kwargs)

        for manager in self.managers:
            setattr(
                self.manager_set,
                manager.__short_name__,
                ModelManagerSetMethod(manager, self.manager_set),
            )

    def get_managers(self) -> ModelManagerSet:
        return self.manager_set


UserManagers = ModelManagerFactory(
    User, [BaseModelManager, DateQueryModelManager]
).get_managers()

BudgetManagers = ModelManagerFactory(
    Budget, [BaseModelManager, DateQueryModelManager]
).get_managers()

CategorytManagers = ModelManagerFactory(
    EntryCategory,
    [BaseModelManager, DateQueryModelManager],
    order_by=["-last_used", "id"],
).get_managers()
