import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable, Type

from sqlalchemy import select, text
from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.sql import column

from app.utils import DateGen

from .base import AbstractBaseModel


@dataclass
class AbstractModelManager(ABC):
    """Interface for creating model managers."""

    model: Type[AbstractBaseModel]
    session: Session | scoped_session

    @abstractmethod
    def get(self, id: int) -> Type[AbstractBaseModel] | None:
        """Select one `self.model` object by it's id."""
        pass

    @abstractmethod
    def get_by(self, **kwargs) -> Type[AbstractBaseModel] | None:
        """Select one `self.model` object by kwargs."""
        pass

    @abstractmethod
    def all(self, **kwargs) -> Iterable[Type[AbstractBaseModel]]:
        """Select all `self.model` objects."""
        pass

    @abstractmethod
    def update(self, id: int, **kwargs) -> bool:
        """Update one `self.model` object with given id with given kwargs."""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete one `self.model` object with given id."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Count number of all `self.model` objects."""
        pass

    @abstractmethod
    def exists(self, id: int) -> bool:
        """Tell wether `self.model` object with given id exists or not."""
        pass


class BaseModelManager(AbstractModelManager):
    def __init__(
        self,
        model: Type[AbstractBaseModel],
        session: Session | scoped_session = None,
        /,
    ) -> None:
        self.model = model
        self.session = session

    def __call__(self, session: Session | scoped_session) -> None:
        """Allow `session` be associated
        with manager after it's creation.

        #### Example:
        create manger and leave it for later use
        `manager = BaseManager(BaseModel)`

        when you obtain session (e.g. via middleware)
        associate it with manager
        `manger(request.session)`
        `manger.some_method()`
        """
        if self.session is None and isinstance(
            session, (Session, scoped_session)
        ):
            self.session = session

    def get(self, id: int) -> Type[AbstractBaseModel] | None:
        """Retrieve `self.model` object."""
        return self.session.get(self.model, id)

    def get_by(self, **kwargs) -> Type[AbstractBaseModel] | None:
        """Retrieve `self.model` object filtered by kwargs."""
        if valid_kwargs := self.clean_kwargs(kwargs):
            return (
                self.session.query(self.model)
                .filter_by(**valid_kwargs)
                .first()
            )

    def all(self) -> Query[Type[AbstractBaseModel]]:
        """Retrieve all `self.model` objets."""
        return self.session.query(self.model)

    def list(self) -> list[Type[AbstractBaseModel]]:
        """Retrieve all `self.model` objets in list."""
        return self.all().all()

    def update(
        self,
        id: int,
        *,
        commit: bool = True,
        **kwargs,
    ) -> bool:
        """Update `self.model` object."""
        if valid_kwargs := self.clean_kwargs(kwargs):
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

    def count(self) -> int:
        """Calculate number of all `self.model` objects."""
        return self.session.query(self.model.id).count()

    def exists(self, id: int) -> bool:
        """Tell wether `self.model` object with given id exists or not."""
        return bool(
            self.session.scalar(select(self.model.id).filter_by(id=id))
        )

    def clean_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        return {
            fieldname: value
            for fieldname, value in kwargs.items()
            if fieldname in self.model.fieldnames
        }


class OrderedQueryManager(BaseModelManager):
    def __init__(self, *args, order_by: list[str]):
        self._order_by = order_by
        return super().__init__(*args)

    def all(self, reverse: bool = False) -> Query[Type[AbstractBaseModel]]:
        """Retrieve all `model` instances in ordered query.
        Use `reverse=True` to sort query in descending order.
        """
        qs = super().all()
        return (
            qs.order_by(text(self.inverse_order_by))
            if reverse
            else qs.order_by(text(self.order_by))
        )

    def list(self, reverse: bool = False) -> list[Type[AbstractBaseModel]]:
        """Retrieve all `self.model` objets in list."""
        return self.all(reverse=reverse).all()

    def first_n(self, n: int) -> Query[Type[AbstractBaseModel]]:
        """Retrieve specific number of `model` instances
        sorted in ascending order.
        """
        return self._fetch_n(n, self.order_by)

    def last_n(self, n: int) -> Query[Type[AbstractBaseModel]]:
        """Retrieve specific number of `model` instances
        sorted in descending order.
        """
        return self._fetch_n(n, self.inverse_order_by)

    def first(self) -> Type[AbstractBaseModel] | None:
        """Retrieve first `model` instance in ascending query."""
        return self.first_n(1).one_or_none()

    def last(self) -> Type[AbstractBaseModel] | None:
        """Retrieve last `model` instance in discending query."""
        return self.last_n(1).one_or_none()

    def _fetch_n(
        self, n: int, order_by: str = ""
    ) -> Query[Type[AbstractBaseModel]]:
        return self._fetch(order_by).limit(n)

    def _fetch(self, order_by: str = "") -> Query[Type[AbstractBaseModel]]:
        return self.session.query(self.model).order_by(text(order_by))

    @property
    def order_by(self) -> str:
        return ", ".join(self._order_by)

    @property
    def inverse_order_by(self):
        return ", ".join(
            (
                item.removesuffix(" desc")
                if item.endswith(" desc")
                else item + " desc"
                for item in self._order_by
            )
        )


class DateQueryManager(OrderedQueryManager):
    def __init__(self, *args, datefield: str = "created_at", **kwargs):
        self._datefield = datefield
        return super().__init__(*args, **kwargs)

    # TODO: `date_info` must be added via middleware

    def today(
        self, date_info: DateGen, reverse: bool = False
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.date_range, reverse)

    def yesterday(
        self, date_info: DateGen, reverse: bool = False
    ) -> Query[Type[AbstractBaseModel]]:
        return self._between(*date_info.yesterday_range, reverse)

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
        order_by = self.inverse_order_by if reverse else self.order_by
        return self._fetch(order_by).filter(
            column(self._datefield).between(start, end)
        )
