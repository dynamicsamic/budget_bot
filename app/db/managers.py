import datetime as dt
import logging
import operator as operators
import re
from typing import Any, Callable, List, Literal, Sequence, Type

from sqlalchemy import Date, DateTime, and_
from sqlalchemy import func as sql_func
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import UnaryExpression

from app.db.base import AbstractBaseModel
from app.utils import DateGen

from .base import AbstractBaseModel
from .exceptions import (
    InvalidDateField,
    InvalidFilter,
    InvalidOrderByValue,
    InvalidSumField,
    ModelInstanceCreateError,
)
from .models import Budget, Entry, EntryCategory, User

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(
        self,
        model: Type[AbstractBaseModel],
        session: Session | scoped_session = None,
        order_by: Sequence[str] = ["created_at", "id"],
        filters: Sequence[str] = None,  #  like ["id>2", "sum == 1"]
        datefield: str = "created_at",
    ) -> None:
        self.model = model
        self.session = session
        self._order_by = order_by
        self._filters = filters
        self._datefield = datefield
        self._validate()

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

    @property
    def order_by(self) -> Sequence[str]:
        return self._order_by

    @order_by.setter
    def order_by(self, order_by_: Sequence[str]) -> None:
        self._validate_order_by(order_by_)
        self._order_by = order_by_

    @property
    def filters(self) -> Sequence[str]:
        return self._filters

    @filters.setter
    def filters(self, filters_: Sequence[str]) -> None:
        self._validate_filters(filters_)
        self._filters = filters_

    @property
    def datefield(self) -> str:
        return self._datefield

    @datefield.setter
    def datefield(self, datefield_: str) -> None:
        self._validate_datefield(datefield_)
        self._datefield = datefield_

    def create(self, **kwargs) -> Type[AbstractBaseModel] | None:
        """Create an instance of `'self.model`.
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

    def get(self, id_: int) -> Type[AbstractBaseModel] | None:
        """Retrieve `self.model` object."""
        return self.session.get(self.model, id_)

    def get_by(self, **kwargs) -> Type[AbstractBaseModel] | None:
        """Retrieve `self.model` object filtered by kwargs."""
        if valid_kwargs := self._clean_kwargs(kwargs):
            return (
                self.session.query(self.model)
                .filter_by(**valid_kwargs)
                .first()
            )

    def all(self, reverse: bool = False) -> Query[Type[AbstractBaseModel]]:
        """Retrieve all `self.model` objets."""
        return self._fetch(reverse=reverse)

    def list(self, reverse: bool = False) -> List[Type[AbstractBaseModel]]:
        """Retrieve all `self.model` objets in list."""
        return self._fetch(reverse=reverse).all()

    def select(
        self,
        *,
        filters: Sequence[str],
        reverse: bool = False,
    ) -> Query[Type[AbstractBaseModel]]:
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
    ) -> Type[AbstractBaseModel] | None:
        """Retrieve first `model` instance in ascending query."""
        return self.first_n(1, filters=filters).one_or_none()

    def last(
        self, *, filters: Sequence[str] = None
    ) -> Type[AbstractBaseModel] | None:
        """Retrieve last `model` instance in discending query."""
        return self.last_n(1, filters=filters).one_or_none()

    def first_n(
        self, n: int, *, filters: Sequence[str] = None
    ) -> Query[Type[AbstractBaseModel]]:
        """Retrieve specific number of `model` instances
        sorted in ascending order.
        """
        return self._fetch_n(n, filters)

    def last_n(
        self, n: int, *, filters: Sequence[str] = None
    ) -> Query[Type[AbstractBaseModel]]:
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

    def _fetch(
        self, filters: Sequence[str] = None, reverse: bool = False
    ) -> Query[Type[AbstractBaseModel]]:
        q = self.session.query(self.model).order_by(
            *self._compile_order_by(reverse)
        )
        filter_by = self._compile_filter_expr(filters)
        if filter_by is not None:
            return q.filter(filter_by)

        return q

    def _fetch_n(
        self, n: int, filters: Sequence[str] = None, reverse: bool = False
    ) -> Query[Type[AbstractBaseModel]]:
        return self._fetch(filters, reverse).limit(n)

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

    @property
    def _order_by_dict(self) -> dict[str, Literal["asc", "desc"]]:
        return self._transform_to_order_by_dict(self.order_by)

    @property
    def _reversed_order_by_dict(self) -> dict[str, Literal["asc", "desc"]]:
        return {
            attr: "desc" if order == "asc" else "asc"
            for attr, order in self._order_by_dict.items()
        }

    @staticmethod
    def _transform_to_order_by_dict(
        order_by: Sequence[str],
    ) -> dict[str, Literal["asc", "desc"]]:
        order_by_dict = {}
        for attr in order_by:
            if attr.startswith("-"):
                order_by_dict[attr[1:].strip()] = "desc"
            elif attr.endswith("-"):
                order_by_dict[attr[:-1].strip()] = "desc"
            else:
                order_by_dict[attr.strip()] = "asc"
        return order_by_dict

    def _compile_filter_expr(self, filters: Sequence[str] = None):
        filters = filters or self.filters

        if not filters:
            return

        return and_(
            True, *self._validate_filters(filters, return_filters=True)
        )

    def _validate(self):
        self._validate_order_by(self._order_by)
        self._validate_filters()
        self._validate_datefield(self._datefield)

    @staticmethod
    def _check_iterable(check_value: Any, exception: Exception):
        if not hasattr(check_value, "__iter__"):
            raise exception(
                f"{check_value} must be a sequence, not a {type(check_value)}"
            )

    def _validate_order_by(self, order_by: Sequence[str]):
        self._check_iterable(order_by, InvalidOrderByValue)
        order_by_dict = self._transform_to_order_by_dict(order_by)
        if invalid_fields := set(order_by_dict.keys()) - self.model.fieldnames:
            raise InvalidOrderByValue(
                f"""Following values can not be 
                used as `order_by` args: {', '.join(invalid_fields)}."""
            )

    def _validate_filters(
        self, filters: Sequence[str] = None, return_filters: bool = False
    ):
        filters = filters or self.filters

        validated = []
        if filters:
            self._check_iterable(filters, InvalidFilter)
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

                attr = getattr(self.model, attr_.strip(), None)
                operator = getattr(
                    operators, valid_signs.get(sign, "None"), None
                )

                if attr is None:
                    raise InvalidFilter(
                        f"""Model `{self.model}` 
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

    def _set_default_order_by(self):
        self._order_by = ["created_at", "id"]

    def _reset_filters(self):
        self._filters = None

    def _set_default_datefield(self):
        self._datefield = "created_at"


class DateQueryManager(ModelManager):
    def today(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.date_range, filters, reverse)

    def yesterday(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.yesterday_range, filters, reverse)

    def this_week(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.week_range, filters, reverse)

    def this_month(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.month_range, filters, reverse)

    def this_year(
        self,
        date_info: DateGen,
        *,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.year_range, filters, reverse)

    def _between(
        self,
        start: dt.datetime | dt.date,
        end: dt.datetime | dt.date,
        filters: Sequence[str] = None,
        reverse: bool = False,
    ) -> Query[Type[AbstractBaseModel]]:
        """Fetch all instances of `model` filtered
        between given borders.
        """
        date_column = getattr(self.model, self.datefield)
        return self._fetch(filters, reverse).filter(
            date_column.between(start, end)
        )


class ExtendedQuery:
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


class EntryManager(DateQueryManager):
    def __getattribute__(self, __name: str) -> Any:
        """Decorate methods that return `Query` with
        `self.extend_query` decorator.
        """
        attr = super().__getattribute__(__name)

        if callable(attr):
            return_type = attr.__annotations__.get("return")
            if return_type is Query:
                try:
                    return self.extend_query(attr)
                except Exception:
                    return attr
        return attr

    def extend_query(self, f: Callable[..., Query]):
        """Add `ExtendedQuery` methods as `ext` attribute
        to a query.
        """

        def inner(*args, **kwargs):
            query = f(*args, **kwargs)
            setattr(query, "ext", ExtendedQuery(self.model, "sum", query))
            return query

        return inner


user_manager = DateQueryManager(User)
budget_manager = DateQueryManager(Budget)
category_manager = DateQueryManager(
    EntryCategory, order_by=["last_used", "id"]
)
entry_manager = EntryManager(
    Entry,
    datefield="transaction_date",
    order_by=["-transaction_date", "created_at"],
)


class ModelManagerStore:
    managers = {
        "user_manager": user_manager,
        "budget_manager": budget_manager,
        "category_manager": category_manager,
        "entry_manager": entry_manager,
    }

    @classmethod
    def as_flags(cls, *names: str) -> Sequence[str]:
        name_to_manager = {
            "user": "user_manager",
            "budget": "budget_manager",
            "category": "category_manager",
            "entry": "entry_manager",
        }

        return_managers = [
            name_to_manager.get(name) for name in names
        ] or cls.managers.values()

        return {"model_managers": return_managers}

    @classmethod
    def get(cls, name: str) -> ModelManager:
        return cls.managers.get(name)
