import datetime as dt
import operator
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal, Sequence, Type

from sqlalchemy import Date, DateTime, and_
from sqlalchemy import func as sql_func
from sqlalchemy import select, text
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
)
from .models import Entry, User


class ModelManager:
    def __init__(
        self,
        model: Type[AbstractBaseModel],
        session: Session | scoped_session = None,
        order_by: Sequence[str] = ["created_at", "last_updated", "id"],
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
        if self.session is None and isinstance(
            session, (Session, scoped_session)
        ):
            self.session = session

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

    def create(self, **kwargs):
        pass

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

    def all(self) -> Query[Type[AbstractBaseModel]]:
        """Retrieve all `self.model` objets."""
        return self._fetch()

    def list(self) -> list[Type[AbstractBaseModel]]:
        """Retrieve all `self.model` objets in list."""
        return self._fetch().all()

    def select(
        self,
        reverse: bool = False,
        *filters: str,
    ) -> Query[Type[AbstractBaseModel]]:
        return self._fetch(reverse, *filters)

    def count(self) -> int:
        """Calculate number of all `self.model` objects."""
        return self.session.query(self.model.id).count()

    def exists(self, id: int) -> bool:
        """Tell wether `self.model` object with given id exists or not."""
        return bool(
            self.session.scalar(select(self.model.id).filter_by(id=id))
        )

    def first(self, *filters: str) -> Type[AbstractBaseModel] | None:
        """Retrieve first `model` instance in ascending query."""
        return self.first_n(1, *filters).one_or_none()

    def last(self, *filters: str) -> Type[AbstractBaseModel] | None:
        """Retrieve last `model` instance in discending query."""
        return self.last_n(1, *filters).one_or_none()

    def first_n(self, n: int, *filters: str) -> Query[Type[AbstractBaseModel]]:
        """Retrieve specific number of `model` instances
        sorted in ascending order.
        """
        return self._fetch_n(n, *filters)

    def last_n(self, n: int, *filters: str) -> Query[Type[AbstractBaseModel]]:
        """Retrieve specific number of `model` instances
        sorted in descending order.
        """
        return self._fetch_n(n, True, *filters)

    def _clean_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        return {
            fieldname: value
            for fieldname, value in kwargs.items()
            if fieldname in self.model.fieldnames
        }

    def _fetch(
        self, reverse: bool = False, *filters: str
    ) -> Query[Type[AbstractBaseModel]]:
        q = self.session.query(self.model).order_by(
            text(self._compile_order_by(reverse))
        )
        filter_by = self._compile_filter_expr(filters)
        if filter_by is not None:
            return q.filter(filter_by)

        return q

    def _fetch_n(
        self, n: int, reverse: bool = False, *filters: str
    ) -> Query[Type[AbstractBaseModel]]:
        return self._fetch(reverse, *filters).limit(n)

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

        self._validate_filters(filters)

        # TODO: need to include filter value in quotes
        # to avoid weird bugs with dates
        return and_(True, *[text(filter) for filter in filters])

    def _validate(self):
        self._validate_order_by()
        self._validate_filters()
        self._validate_datefield()

    def _validate_order_by(self, order_by: Sequence[str] = None):
        order_by = order_by or self.order_by
        cleaned_values = {val.strip() for val in order_by}
        if invalid_fields := cleaned_values - self.model.fieldnames:
            raise InvalidOrderByValue(
                f"""Following values can not be 
                used as `order_by` args: {', '.join(invalid_fields)}."""
            )

    def _validate_filters(self, filters: Sequence[str] = None):
        filters = filters or self.filters
        if filters:
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
                    attr, sign, value = re.split("([<>!=]+)", filter)
                except ValueError:
                    raise InvalidFilter(
                        """Filter should follow pattern:
                          <model_attribute><compare_operator><value>.
                          Example: `sum>1`, `id == 2`"""
                    )

                if not hasattr(self.model, attr.strip()):
                    raise InvalidFilter(
                        f"""Model `{self.model}` 
                        does not have `{attr}` atribute."""
                    )

                elif not hasattr(operator, valid_signs.get(sign, "None")):
                    raise InvalidFilter(f"Invalid comparing sign: `{sign}`")

                elif not value:
                    raise InvalidFilter("Filter must have a value.")

    def _validate_datefield(self, datefield_: str = None):
        datefield_ = datefield_ or self._datefield
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


class DateQueryManager(ModelManager):
    def today(
        self, date_info: DateGen, reverse: bool = False
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.date_range, reverse)

    def yesterday(
        self,
        date_info: DateGen,
        reverse: bool = False,
        *filters: str,
    ) -> Query[Type[AbstractBaseModel]]:
        return self._new_between(*date_info.yesterday_range, reverse, *filters)

    def this_week(
        self, date_info: DateGen, reverse: bool = False
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.week_range, reverse)

    def this_month(
        self, date_info: DateGen, reverse: bool = False
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.month_range, reverse)

    def this_year(
        self, date_info: DateGen, reverse: bool = False
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.year_range, reverse)

    def _between(
        self,
        start: dt.datetime | dt.date,
        end: dt.datetime | dt.date,
        reverse: bool = False,
    ) -> Query[Type[AbstractBaseModel]]:
        """Fetch all instances of `model` filtered
        between given borders.
        """
        order_by = (
            self._reverse_order_by if reverse else self._prepare_order_by
        )
        return self._fetch(order_by).filter(
            column(self._datefield).between(start, end)
        )

    def _new_between(
        self,
        start: dt.datetime | dt.date,
        end: dt.datetime | dt.date,
        reverse: bool = False,
        *filters: str,
    ) -> Query[Type[AbstractBaseModel]]:
        """Fetch all instances of `model` filtered
        between given borders.
        """
        return self._fetch(reverse, *filters).filter(
            column(self._datefield).between(start, end)
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
        return q.with_entities(sql_func.sum(self.sum_field)).scalar()


class EntryManager(DateQueryManager):
    def __getattribute__(self, __name: str) -> Any:
        """Make methods that return `Query` provide
        additional `income`, `expenses` and `total` attributes,
        so you can do:
            `query = self.method(*args, **kwargs).income`
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

    def extend_query(self, f: Callable):
        def inner(*args, **kwargs):
            query = f(*args, **kwargs)
            setattr(query, "ext", ExtendedQuery(self.model, "sum", query))
            return query

        return inner


user_manager = DateQueryManager(User)

entry_manager = EntryManager(
    Entry,
    datefield="transaction_date",
    order_by=["transaction_date", "created_at"],
)
