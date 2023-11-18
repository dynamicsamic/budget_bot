import datetime as dt
import logging
from dataclasses import dataclass
from typing import Any, Callable, List, Literal, Optional, Self, Sequence, Type

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.functional_validators import model_validator
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql._typing import _DMLColumnArgument
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement, UnaryExpression

from app.db.exceptions import InvalidDBSession, InvalidFilter, InvalidOrderByValue
from app.db.models.base import AbstractBaseModel
from app.utils import DateGen, _ComparingExpression, _OrderByValue

from .utils import (
    FilterExpression,
    ManagerFieldDescriptor,
    SumExtendedQuery,
    transform_to_order_by_dict,
)
from .validation import (
    check_iterable,
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




class PydanticManager(BaseModel):
    """Basic interface for performig database operations.

    Supports CRUD operations and let's you perform more precise queries
    like fetch first and last added items, learn if a instance with
    give kwargs exists and more.

    All SELECT queries are ordered and support filtering either via the
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
        filters: A sequence of comparing expressions which provide
            query post-filtering. Each expression consists of a model field
            (`e.g. 'id' or 'name')`, a comparing sign (`e.g. '>' or '=='`) and
            a value (`e.g. '2' or 'jack'`).
            Passing values to `filters` sets up manager-level query filtering.
            Manager-level filtering will be replaced with method-level
            filtering when providing arguments to `filters` parameter in some
            instance methods like `select`, `all`, `first` and others.
            Valid arguments may include `['id>2', 'sum == 1']`
    """

    __short_name__ = "test"

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        strict=True,
        validate_assignment=True,
    )

    model: Type[AbstractBaseModel]
    session: Optional[Session | scoped_session] = DEFAULT_SESSION
    order_by: Sequence[_OrderByValue] = DEFAULT_ORDER_BY
    filters: Optional[Sequence[_ComparingExpression]] = DEFAULT_FILTERS

    @model_validator(mode="after")
    def validate_session(self):
        if self.session is None:
            pass

        elif not self.session.is_active:
            raise ValidationError(
                "Inactive session detected! `session` must be active."
            )
        return self

    @model_validator(mode="after")
    def validate_order_by(self):
        order_by_dict = transform_to_order_by_dict(self.order_by)
        if invalid_fields := set(order_by_dict.keys()) - self.model.fieldnames:
            raise InvalidOrderByValue(
                f"""Following values can not be
            used as `order_by` args: {', '.join(invalid_fields)}."""
            )
        return self

    @model_validator(mode="after")
    def validate_filters(self):
        if self.filters is not None:
            for expression in self.filters:
                FilterExpression(expression, self.model).validate()
        return self

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
            kwargs: A mapping of `model's` attribute names (fields) that should be updated
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
            kwargs: A mapping of `model's` attribute names (fields)
            to their values.

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
        filters: Optional[Sequence[_ComparingExpression]],
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Produce a SELECT query with arbitrary filtering.

        Args:
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlalchemy.Query that contains selected `self.model` instances.
        """
        return self._fetch(filters, reverse)

    def count(
        self, *, filters: Optional[Sequence[_ComparingExpression]] = None
    ) -> int:
        """Calculate the number of model instances filtered by provided values.
        If no filters provided, calculate the number of all model instances.

        Args:
            filters: Sequence of comparing expressions.

        Returns:
            Number of model instances.

        Examples:
            ```
            manager.count()
            ```
        or
            ```
            manager.count(filters=["sum>100"])
            ```
        """
        return self._fetch(filters).count()

    def exists(self, id_: int = 0, **kwargs: Any) -> bool:
        """Find out if a model instance with provided id or kwargs exists.

        Args:
            id_: Instance `id` field.
            kwargs: A mapping of `model's` attribute names (fields)
            to their values.

        Returns:
            True if an instance exists, False otherwise.

        Examples:
            ```
            manager.exists(53)
            ```
        or
            ```
            manager.exists(budget_id=25)
            ```
        """
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
        self, *, filters: Optional[Sequence[_ComparingExpression]] = None
    ) -> AbstractBaseModel | None:
        """Fetch first added `model` instance.

        Args:
            filters: Sequence of comparing expressions.
        Returns:
            `self.model` instance or None.
        """
        return self.first_n(1, filters=filters).one_or_none()

    def last(
        self, *, filters: Optional[Sequence[_ComparingExpression]] = None
    ) -> AbstractBaseModel | None:
        """Fetch last added `model` instance.

        Args:
            filters: Sequence of comparing expressions.

        Returns:
            `self.model` instance or None.
        """
        return self.last_n(1, filters=filters).one_or_none()

    def first_n(
        self,
        n: int,
        *,
        filters: Optional[Sequence[_ComparingExpression]] = None,
    ) -> Query[AbstractBaseModel]:
        """Fetch specified number of the earliest `model` instances.

        Args:
            n: Number of `self.model` instances that a query should contain.
            filters: Sequence of comparing expressions.

        Returns:
            sqlalchemy.Query that contains specified number
            of `self.model` instances.
        """
        return self._fetch_n(n, filters)

    def last_n(
        self,
        n: int,
        *,
        filters: Optional[Sequence[_ComparingExpression]] = None,
    ) -> Query[AbstractBaseModel]:
        """Fetch specified number of the most recent `model` instances.

        Args:
            n: Number of `self.model` instances that a query should contain.
            filters: Sequence of comparing expressions.

        Returns:
            sqlalchemy.Query that contains specified number
            of `self.model` instances.
        """
        return self._fetch_n(n, filters, True)

    def _fetch(
        self,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Basic SELECT query with ordering and optional filtering.

        This is the underlying query for almost all SELECT methods
        that are part of the public API of this class.

        Args:
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlalchemy.Query that contains selected `self.model` instances.
        """
        q = self.session.query(self.model).order_by(
            *self._compile_order_by(reverse)
        )
        filter_by = self._compile_filter_expr(filters)
        if filter_by is not None:
            return q.filter(filter_by)

        return q

    def _fetch_n(
        self,
        n: int,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Basic SELECT query with ordering, optional filtering and a limit.

        Args:
            n: Number of `self.model` instances that a query should contain.
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlalchemy.Query that contains specified number
            of `self.model` instances.
        """
        return self._fetch(filters, reverse).limit(n)

    def _compile_order_by(
        self, reverse: bool
    ) -> List[InstrumentedAttribute | UnaryExpression]:
        """Construct a sequence of model attributes
        to be used in ORDER BY clause.

        Args:
            reverse: Flag to reverse the default ordering of fields.

        Returns:
            List of sqlalchemy model attributes.
        """
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
        self, filters: Sequence[_ComparingExpression] = None
    ) -> ColumnElement[True] | None:
        """Construct a filtering expression to be used in WHERE clause.

        All parts of the `filters` argument will be glued together by
        the AND expression. Thus filters will generate a matching
        expression only if all the `filters` parts are true.

        Args:
            filters: Sequence of comparing expressions.

        Returns:
            sqlalchemy and_ expression that contains validated filters.
        """
        filters = filters or self.filters

        if not filters:
            return

        return and_(True, *self._collect_filters(filters))

    def _collect_filters(
        self, filters: Sequence[_ComparingExpression]
    ) -> List[BinaryExpression]:
        """Convert filters into list of expressions for further processing.

        If any of expressions in filters is invalid,
        InvalidFilter will be raised

        Args:
            filters: A sequence of comparing expressions.

        Returns:
            List of built filter expressions.
        """
        check_iterable(filters, InvalidFilter)
        return [
            FilterExpression(expression, self.model).build()
            for expression in filters
        ]

    def _clean_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Filter kwargs from keys not related to `model` fields.

        Args:
            kwargs: A mapping of `model's` attribute names (fields)
            to their values.

        Returns:
            A dictionary of filtered model fields and their values.
        """
        return {
            fieldname: value
            for fieldname, value in kwargs.items()
            if fieldname in self.model.fieldnames
        }

    @property
    def _order_by_dict(self) -> dict[_OrderByValue, Literal["asc", "desc"]]:
        return transform_to_order_by_dict(self.order_by)

    @property
    def _reversed_order_by_dict(
        self,
    ) -> dict[_OrderByValue, Literal["asc", "desc"]]:
        return {
            attr: "desc" if order == "asc" else "asc"
            for attr, order in self._order_by_dict.items()
        }

    def _set_default_order_by(self) -> None:
        self.order_by = DEFAULT_ORDER_BY

    def _reset_filters(self) -> None:
        self.filters = DEFAULT_FILTERS


@dataclass
class BaseModelManager:
    """Basic interface for performig database operations.

    Supports CRUD operations and let's you perform more precise queries
    like fetch first and last added items, learn if a instance with
    give kwargs exists and more.

    All SELECT queries are ordered and support filtering either via the
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
        filters: A sequence of comparing expressions which provide
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
    session: Optional[Session | scoped_session] = ManagerFieldDescriptor(
        default=DEFAULT_SESSION, validators=[validate_db_session]
    )
    order_by: Optional[Sequence[_OrderByValue]] = ManagerFieldDescriptor(
        default=DEFAULT_ORDER_BY, validators=[validate_order_by]
    )
    filters: Optional[Sequence[_ComparingExpression]] = ManagerFieldDescriptor(
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
            kwargs: A mapping of `model's` attribute names (fields) that should be updated
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
            kwargs: A mapping of `model's` attribute names (fields)
            to their values.

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
        filters: Optional[Sequence[_ComparingExpression]],
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Produce a SELECT query with arbitrary filtering.

        Args:
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlalchemy.Query that contains selected `self.model` instances.
        """
        return self._fetch(filters, reverse)

    def count(
        self, *, filters: Optional[Sequence[_ComparingExpression]] = None
    ) -> int:
        """Calculate the number of model instances filtered by provided values.
        If no filters provided, calculate the number of all model instances.

        Args:
            filters: Sequence of comparing expressions.

        Returns:
            Number of model instances.

        Examples:
            ```
            manager.count()
            ```
        or
            ```
            manager.count(filters=["sum>100"])
            ```
        """
        return self._fetch(filters).count()

    def exists(self, id_: int = 0, **kwargs: Any) -> bool:
        """Find out if a model instance with provided id or kwargs exists.

        Args:
            id_: Instance `id` field.
            kwargs: A mapping of `model's` attribute names (fields)
            to their values.

        Returns:
            True if an instance exists, False otherwise.

        Examples:
            ```
            manager.exists(53)
            ```
        or
            ```
            manager.exists(budget_id=25)
            ```
        """
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
        self, *, filters: Optional[Sequence[_ComparingExpression]] = None
    ) -> AbstractBaseModel | None:
        """Fetch first added `model` instance.

        Args:
            filters: Sequence of comparing expressions.
        Returns:
            `self.model` instance or None.
        """
        return self.first_n(1, filters=filters).one_or_none()

    def last(
        self, *, filters: Optional[Sequence[_ComparingExpression]] = None
    ) -> AbstractBaseModel | None:
        """Fetch last added `model` instance.

        Args:
            filters: Sequence of comparing expressions.

        Returns:
            `self.model` instance or None.
        """
        return self.last_n(1, filters=filters).one_or_none()

    def first_n(
        self,
        n: int,
        *,
        filters: Optional[Sequence[_ComparingExpression]] = None,
    ) -> Query[AbstractBaseModel]:
        """Fetch specified number of the earliest `model` instances.

        Args:
            n: Number of `self.model` instances that a query should contain.
            filters: Sequence of comparing expressions.

        Returns:
            sqlalchemy.Query that contains specified number
            of `self.model` instances.
        """
        return self._fetch_n(n, filters)

    def last_n(
        self,
        n: int,
        *,
        filters: Optional[Sequence[_ComparingExpression]] = None,
    ) -> Query[AbstractBaseModel]:
        """Fetch specified number of the most recent `model` instances.

        Args:
            n: Number of `self.model` instances that a query should contain.
            filters: Sequence of comparing expressions.

        Returns:
            sqlalchemy.Query that contains specified number
            of `self.model` instances.
        """
        return self._fetch_n(n, filters, True)

    def _fetch(
        self,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Basic SELECT query with ordering and optional filtering.

        This is the underlying query for almost all SELECT methods
        that are part of the public API of this class.

        Args:
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlalchemy.Query that contains selected `self.model` instances.
        """
        q = self.session.query(self.model).order_by(
            *self._compile_order_by(reverse)
        )
        filter_by = self._compile_filter_expr(filters)
        if filter_by is not None:
            return q.filter(filter_by)

        return q

    def _fetch_n(
        self,
        n: int,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Basic SELECT query with ordering, optional filtering and a limit.

        Args:
            n: Number of `self.model` instances that a query should contain.
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlalchemy.Query that contains specified number
            of `self.model` instances.
        """
        return self._fetch(filters, reverse).limit(n)

    def _compile_order_by(
        self, reverse: bool
    ) -> List[InstrumentedAttribute | UnaryExpression]:
        """Construct a sequence of model attributes
        to be used in ORDER BY clause.

        Args:
            reverse: Flag to reverse the default ordering of fields.

        Returns:
            List of sqlalchemy model attributes.
        """
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
        self, filters: Sequence[_ComparingExpression] = None
    ) -> ColumnElement[True] | None:
        """Construct a filtering expression to be used in WHERE clause.

        All parts of the `filters` argument will be glued together by
        the AND expression. Thus filters will generate a matching
        expression only if all the `filters` parts are true.

        Args:
            filters: Sequence of comparing expressions.

        Returns:
            sqlalchemy and_ expression that contains validated filters.
        """
        filters = filters or self.filters

        if not filters:
            return

        return and_(True, *self._collect_filters(filters))

    def _collect_filters(
        self, filters: Sequence[_ComparingExpression]
    ) -> List[BinaryExpression]:
        """Convert filters into list of expressions for further processing.

        If any of expressions in filters is invalid,
        InvalidFilter will be raised

        Args:
            filters: A sequence of comparing expressions.

        Returns:
            List of built filter expressions.
        """
        check_iterable(filters, InvalidFilter)
        return [
            FilterExpression(expression, self.model).build()
            for expression in filters
        ]

    def _clean_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Filter kwargs from keys not related to `model` fields.

        Args:
            kwargs: A mapping of `model's` attribute names (fields)
            to their values.

        Returns:
            A dictionary of filtered model fields and their values.
        """
        return {
            fieldname: value
            for fieldname, value in kwargs.items()
            if fieldname in self.model.fieldnames
        }

    @property
    def _order_by_dict(self) -> dict[_OrderByValue, Literal["asc", "desc"]]:
        return transform_to_order_by_dict(self.order_by)

    @property
    def _reversed_order_by_dict(
        self,
    ) -> dict[_OrderByValue, Literal["asc", "desc"]]:
        return {
            attr: "desc" if order == "asc" else "asc"
            for attr, order in self._order_by_dict.items()
        }

    def _set_default_order_by(self) -> None:
        self.order_by = DEFAULT_ORDER_BY

    def _reset_filters(self) -> None:
        self.filters = DEFAULT_FILTERS


@dataclass
class DateRangeQueryManager(BaseModelManager):
    """BaseModelManager extended with methods for
    making queries with datetime ranges.

    Attributes:
        model: A subclass of `app.models.base.AbstractBaseModel`
        session: An instance of `sqlalchemy.orm.Session` or `scoped_session`
            Initially is set to None, and should be passed to a manager to
            connect it to a database and perform real operations.
        order_by: A sequence of valid model fields which shape the order of
            performed db queries.
            Valid arguments may include `["-id", "created_at", "updated_at-"]`
        filters: A sequence of comparing expressions which provide
            query post-filtering. Each expression consists of a model field
            (`e.g. 'id' or 'name')`, a comparing sign (`e.g. '>' or '=='`) and
            a value (`e.g. '2' or 'jack'`).
            Passing values to `filters` sets up manager-level query filtering.
            Manager-level filtering will be replaced with method-level
            filtering when providing arguments to `filters` parameter in some
            instance methods like `select`, `all`, `first` and others.
            Valid arguments may include `['id>2', 'sum == 1']`
        datefield: The name of model field that is used for making
            date range queries. Must reflect a model attribute of
            sqlalchemy `DATE` or `DATETIME` types. This string will be resolved
            into a real model attribute via `self._date_column` property.
    """

    __short_name__ = "date"

    datefield: Optional[str] = ManagerFieldDescriptor(
        default=DEFAULT_DATEFIELD, validators=[validate_datefield]
    )

    def today(
        self,
        date_info: DateGen,
        *,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Fetch model instances between the start and end of today.

        Args:
            date_info: Instance of DateGen class.
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlclahemy.Query that contains model instances between given gaps.
        """
        return self._between(*date_info.date_range, filters, reverse)

    def yesterday(
        self,
        date_info: DateGen,
        *,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Fetch model instances between the start and end of yesterday.

        Args:
            date_info: Instance of DateGen class.
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlclahemy.Query that contains model instances between given gaps.
        """
        return self._between(*date_info.yesterday_range, filters, reverse)

    def this_week(
        self,
        date_info: DateGen,
        *,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Fetch model instances between the start and end of current week.

        Args:
            date_info: Instance of DateGen class.
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlclahemy.Query that contains model instances between given gaps.
        """
        return self._between(*date_info.week_range, filters, reverse)

    def this_month(
        self,
        date_info: DateGen,
        *,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Fetch model instances between the start and end of current month.

        Args:
            date_info: Instance of DateGen class.
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlclahemy.Query that contains model instances between given gaps.
        """
        return self._between(*date_info.month_range, filters, reverse)

    def this_year(
        self,
        date_info: DateGen,
        *,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Fetch model instances between the start and end of current year.

        Args:
            date_info: Instance of DateGen class.
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlclahemy.Query that contains model instances between given gaps.
        """
        return self._between(*date_info.year_range, filters, reverse)

    def _between(
        self,
        start: dt.datetime | dt.date,
        end: dt.datetime | dt.date,
        filters: Optional[Sequence[_ComparingExpression]] = None,
        reverse: bool = False,
    ) -> Query[AbstractBaseModel]:
        """Fetch `model` instances between given borders.

        This is the underlying method for all public date range methods.

        Args:
            start: The start of a datetime (date) range.
            end: The end of a datetime (date) range.
            filters: Sequence of comparing expressions.
            reverse: Flag to reverse the order of resulting query.

        Returns:
            sqlclahemy.Query that contains model instances between given gaps.
        """
        return self._fetch(filters, reverse).filter(
            self._date_column.between(start, end)
        )

    @property
    def _date_column(self) -> InstrumentedAttribute:
        """Get model attribute by"""
        return getattr(self.model, self.datefield)

    def _set_default_datefield(self):
        self.datefield = DEFAULT_DATEFIELD


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
        self.cashflowfield = DEFAULT_CASHFLOWFIELD
