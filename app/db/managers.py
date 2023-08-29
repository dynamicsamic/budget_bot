import datetime as dt
import operator as operators
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal, Sequence, Type

from sqlalchemy import Date, DateTime, and_
from sqlalchemy import func as sql_func
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.sql import column

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
from .models import Entry, User


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

    def create(self, **kwargs) -> bool:
        if invalid_kwargs := set(kwargs.keys()) - self.model.fieldnames:
            raise ModelInstanceCreateError(
                f"Invalid fields for {self.model.__name__}: {', '.join(invalid_kwargs)}"
            )

        self.session.add(self.model(**kwargs))
        try:
            self.session.commit()
        except SQLAlchemyError:
            raise ModelInstanceCreateError(
                f"Can not create {self.model.__name__} instance. Check provided args."
            )

        return True

    def update(
        self,
        id: int,
        *,
        commit: bool = True,
        **kwargs,
    ) -> bool:
        """Update `self.model` object."""
        if valid_kwargs := self._clean_kwargs(kwargs):
            updated = bool(
                self.session.query(self.model)
                .filter_by(id=id)
                .update(valid_kwargs)
            )
            if updated and commit:
                self.session.commit()
            return updated
        return False

    def delete(self, id: int) -> bool:
        """Delete `self.model` object with given `id`."""
        # TODO: improve this damn thing!
        # emits separate select and delete queries
        # for self.model and each foreign key
        # which is inefficient. Need to implement
        # more efficient algorithm.
        try:
            self.session.delete(self.get(id))
            self.session.commit()
            return True
        except Exception:
            return False

    def get(self, id: int) -> Type[AbstractBaseModel] | None:
        """Retrieve `self.model` object."""
        return self.session.get(self.model, id)

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

    def list(self, reverse: bool = False) -> list[Type[AbstractBaseModel]]:
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

    def exists(self, id: int = None, **kwargs) -> bool:
        """Tell wether `self.model` object with given id exists or not."""
        if id:
            kwargs["id"] = id

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
            text(self._compile_order_by(reverse))
        )
        filter_by = self._compile_filter_expr(filters)
        if filter_by is not None:
            return q.filter(filter_by)

        return q

    def _fetch_n(
        self, n: int, filters: Sequence[str] = None, reverse: bool = False
    ) -> Query[Type[AbstractBaseModel]]:
        return self._fetch(filters, reverse).limit(n)

    def _compile_order_by(self, reverse=bool) -> str:
        return (
            self._reverse_order_by() if reverse else self._prepare_order_by()
        )

    def _prepare_order_by(self) -> str:
        return ", ".join(self.order_by)

    def _reverse_order_by(self) -> str:
        return ", ".join(
            (
                item.removesuffix(" desc")
                if item.endswith(" desc")
                else item + " desc"
                for item in self.order_by
            )
        )

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
        cleaned_values = {val.strip() for val in order_by}
        if invalid_fields := cleaned_values - self.model.fieldnames:
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
# user = user_manager
entry_manager = EntryManager(
    Entry,
    datefield="transaction_date",
    order_by=["transaction_date", "created_at"],
)
