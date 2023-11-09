import datetime as dt
import logging
from dataclasses import dataclass
from types import MethodType
from typing import Any, Callable, List, Literal, Self, Sequence, Type

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, joinedload, scoped_session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql._typing import _DMLColumnArgument
from sqlalchemy.sql.elements import ColumnElement, UnaryExpression

from app.db.exceptions import InvalidDBSession
from app.db.models import Budget, Entry, EntryCategory, User
from app.db.models.base import AbstractBaseModel
from app.utils import DateGen

from .utils import (
    ManagerFieldDescriptor,
    SumExtendedQuery,
    transform_to_order_by_dict,
    validate_cashflowfield,
    validate_datefield,
    validate_db_session,
    validate_filters,
    validate_order_by,
)

logger = logging.getLogger(__name__)

DEFAULT_SESSION = None
DEFAULT_ORDER_BY = ("created_at", "id")
DEFAULT_FILTERS = None
DEFAULT_DATEFIELD = "created_at"
DEFAULT_CASHFLOWFIELD = "sum"


@dataclass
class BaseModelManager:
    """Basic interface for performig database operations.

    Supports CRUD operations and let's you perform more precise queries
    like fetch first and last added items, learn if a instance with
    give kwargs exists and more.

    All select queries are ordered and support filtering either via the
    pre-set `.filters` instance attribute or via passing values to `filters`
    parameter of some methods.

    Attributes:
        model: A subclass of `app.models.base.AbstractBaseModel`
        session: An instance of `sqlalchemy.orm.Session` or `scoped_session`
            Initially is set to None, and should be passed to a manager to
            connect it to a database and perform real operations.
        order_by: A sequence of valid model fields which shape the order of
            performed db queries.
            Valid arguments may include `["-id", "created_at", "updated_at-"]`
        filters: A sequence of comparative expressions which provide
            query post-filtering. Each expression consists of a model field
            (`e.g. 'id' or 'name')`, a comparing sign (`e.g. '>' or '=='`) and
            a value (`e.g. '2' or 'jack'`).
            Passing values to `filters` sets up manager-level query filtering.
            Manager-level filtering will be replaced with method-level
            filtering when providing arguments to `filters` parameter in some
            instance methods like `select`, `all`, `first` and others.
            Valid arguments may include `['id>2', 'sum == 1']`
    """

    __short_name__ = "base"

    model: Type[AbstractBaseModel]
    session: Session | scoped_session = ManagerFieldDescriptor(
        default=DEFAULT_SESSION, validators=[validate_db_session]
    )
    order_by: Sequence[str] = ManagerFieldDescriptor(
        default=DEFAULT_ORDER_BY, validators=[validate_order_by]
    )
    filters: Sequence[str] = ManagerFieldDescriptor(
        default=DEFAULT_FILTERS, validators=[validate_filters]
    )

    def __call__(self, session: Session | scoped_session) -> Self:
        """Shorthand for associating db_session with manager.
        ```
        with db_session() as session:
            middleware.data['some_manager'] = manager(db_session)
        ```

        Args:
            session: an active db_session.

        Returns:
            The instance itself.

        Raises:
            InvalidDBSession: if session is None; if session has invalid type;
            if session is closed.
        """
        if session is None:
            raise InvalidDBSession(
                "Calling manager with `None` session is not allowed."
            )
        self.session = session
        return self

    def create(self, **kwargs: Any) -> AbstractBaseModel | None:
        """Create an instance of `self.model`.

        Args:
            kwargs: A mapping of `model's` attribute (field) names
            to their values.

        Returns:
            The newly created instance or None if error occured.
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
        kwargs: dict[_DMLColumnArgument, Any],
    ) -> bool:
        """Update `self.model` instance with given kwargs.

        Args:
            id_: Instance `id` field.
            kwrags: A mapping of `model's` attribute names (fields) that should be updated
            to new values.

        Returns:
            True if update performed successfully, False otherwise.
        """
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
        """Delete `self.model` instance with given id.

        Args:
            id_: Instance `id` field.

        Returns:
            True if delete performed successfully, False otherwise.
        """
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
        """Fetch `self.model` instance with given id.

        Args:
            id_: Instance `id` field.

        Returns:
            `self.model` instance or None.
        """
        return self.session.get(self.model, id_)

    def get_by(self, **kwargs) -> AbstractBaseModel | None:
        """Fetch `self.model` instance with given kwargs.
        A more flexible variation of `get` method.

        Args:
            kwrags: A mapping of `model's` attribute names (fields) to their values.

        Returns:
            `self.model` instance or None.
        """
        if valid_kwargs := self._clean_kwargs(kwargs):
            return (
                self.session.query(self.model)
                .filter_by(**valid_kwargs)
                .first()
            )

    def all(self, *, reverse: bool = False) -> Query[AbstractBaseModel]:
        """Fetch all instances of `self.model`.

        Args:
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlalchemy.Query that contains all instances of `self.model`.
        """
        return self._fetch(reverse=reverse)

    def list(self, *, reverse: bool = False) -> List[AbstractBaseModel]:
        """Fetch all instances of `self.model` and store them in a list.

        Args:
            reverse: Flag to reverse the order of resulting query.

        Returns:
            Python list that contains all instances of `self.model`.
        """
        return self._fetch(reverse=reverse).all()

    def select(
        self,
        *,
        filters: Sequence[str],
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Produce a SELECT query with arbitrary filtering.

        Args:
            filters: Sequence of compare expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlalchemy.Query that contains selected `self.model` instances.
        """
        return self._fetch(filters, reverse)

    def count(self) -> int:
        """Calculate the number of model instances filtered by provided values.
        If no filters provided, calculate the number of all model instances.

        Args:
            filters: Sequence of compare expressions.

        Returns:
            Number of model instances.
        """
        return self.session.query(self.model.id).count()

    def exists(self, id_: int = 0, **kwargs: Any) -> bool:
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
class DateRangeQueryManager(BaseModelManager):
    """
    BaseModelManager extended with methods for
    making queries with datetime gaps.
    """

    __short_name__ = "date"

    datefield: str = ManagerFieldDescriptor(
        default=DEFAULT_DATEFIELD, validators=[validate_datefield]
    )

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

    def _set_default_datefield(self):
        self._datefield = DEFAULT_DATEFIELD


@dataclass
class CashFlowQueryManager(DateRangeQueryManager):
    __short_name__ = "cashflow"

    cashflowfield: str = ManagerFieldDescriptor(
        default=DEFAULT_CASHFLOWFIELD, validators=[validate_cashflowfield]
    )

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
    elif manager is DateRangeQueryManager:
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
    User, [BaseModelManager, DateRangeQueryManager]
).get_managers()

BudgetManagers = ModelManagerFactory(
    Budget, [BaseModelManager, DateRangeQueryManager]
).get_managers()

CategorytManagers = ModelManagerFactory(
    EntryCategory,
    [BaseModelManager, DateRangeQueryManager],
    order_by=["-last_used", "id"],
).get_managers()
