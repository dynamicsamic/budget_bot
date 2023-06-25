import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable, Type

from sqlalchemy import select, text
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.orm import Query, Session, scoped_session

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

    def all(
        self, to_list: bool = False
    ) -> ScalarResult[Type[AbstractBaseModel]] | list[Type[AbstractBaseModel]]:
        """Retrieve all `self.model` objets
        either in `ScalarResult` or `list` form.
        """
        qs = self.session.scalars(select(self.model))
        return qs.all() if to_list else qs

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
        """Delete `self.model` object."""
        return bool(self.session.query(self.model).filter_by(id=id).delete())

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


class DateQueryManager(BaseModelManager):
    def first_n(self, n: int) -> Query[Type[AbstractBaseModel]]:
        return self._fetch_n(n, self._order_by)

    def last_n(self, n: int) -> Query[Type[AbstractBaseModel]]:
        order_by = self._order_by + " desc"
        return self._fetch_n(n, order_by)

    def first(self) -> Type[AbstractBaseModel] | None:
        return self.first_n(1).one_or_none()

    def last(self) -> Type[AbstractBaseModel] | None:
        return self.last_n(1).one_or_none()

    def between(
        self, start: dt.datetime | dt.date, end: dt.datetime | dt.date
    ) -> Query[Type[AbstractBaseModel]]:
        """Fetch all instances of `model` which were
        created between given date borders.
        """
        if self._is_date_model:
            return self._fetch(self._order_by).filter(
                self.model.date.between(start, end)
            )
        return self._fetch(self._order_by).filter(
            self.model.created_at.between(start, end)
        )

    def _fetch(self, order_by: str = "") -> Query[Type[AbstractBaseModel]]:
        return self.session.query(self.model).order_by(text(order_by))

    def _fetch_n(
        self, n: int, order_by: str = ""
    ) -> Query[Type[AbstractBaseModel]]:
        return self._fetch(order_by).limit(n)

    @property
    def _is_date_model(self) -> bool:
        return hasattr(self.model, "date")

    @property
    def _order_by(self) -> str:
        return "date" if self._is_date_model else "created_at"
