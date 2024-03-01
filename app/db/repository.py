import inspect
import logging
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from typing import Any, Callable, Generator, List, Optional, Type

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.engine.row import Row
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, scoped_session
from sqlalchemy.sql._typing import (
    _DMLColumnArgument,
    _TypedColumnClauseArgument,
)
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.selectable import Select

from app.custom_types import GeneratorResult, _BaseModel, _OrderByValue
from app.exceptions import (
    EmptyModelKwargs,
    InvalidModelArgType,
    InvalidModelAttribute,
    ModelInstanceNotFound,
    RepositoryValidationError,
    UnknownDataBaseException,
)
from app.utils import get_locals

from .models import AbstractBaseModel, Category, CategoryType, Entry, User

logger = logging.getLogger(__name__)


def linked_generator(
    head: _BaseModel, tail: ScalarResult[_BaseModel]
) -> Generator[_BaseModel, _BaseModel, None]:
    yield head
    for i in tail:
        yield i


def attributed_result(f: Callable[..., ScalarResult]):
    def wrapper(*args, **kwargs):
        res = f(*args, **kwargs)
        try:
            head = next(res)
        except StopIteration:
            return GeneratorResult(result=[], is_empty=True, head=None)

        return GeneratorResult(
            result=linked_generator(head, res), is_empty=False, head=head
        )

    wrapper.__signature__ = inspect.signature(f)
    return wrapper


def query_logger(f: Callable[..., ScalarResult]):
    import inspect

    def wrapper(*args, **kwargs):
        res = f(*args, **kwargs)
        logger.info(f"SELECT query emitted by <{inspect.stack()[1].function}>")
        return res

    wrapper.__signature__ = inspect.signature(f)
    return wrapper


@dataclass
class CommonRepository:
    """
    Generic repository for database communication.

    Attributes:
        - `session`: An instance of `sqlalchemy.orm.Session` or `scoped_session`;
        session's `is_active` property must return True.
        - `model`: A subclass of `app.models.base.AbstractBaseModel`.
    """

    session: Session | scoped_session
    model: Type[_BaseModel]

    def __post_init__(self) -> None:
        self._validate()

    def _create(self, **create_kwargs: Any) -> _BaseModel:
        """Create new model instance.

        Args:
            `create_kwargs`: A mapping of model's attribute (field) names
            to their values.

        Returns:
            The newly created instance.

        Raises:
            - Validation errors if `create_kwargs` are invalid
            (see `validate_model_kwargs`).
            - `SQLAlchemyError` exceptions if a db error occured.
            - `UnknownDataBaseException` if an error could not be determined.
        """
        self._validate_model_kwargs(create_kwargs)

        obj = self.model(**create_kwargs)
        try:
            self.session.add(obj)
            self.session.commit()
        except Exception as e:
            if isinstance(e, SQLAlchemyError):
                logger.error(
                    f"SQLAlchemyError during {self.model} "
                    f"instance creation: {e}"
                )
                raise e
            else:
                logger.error(
                    f"Unknown exception during {self.model} "
                    f"instance creation: {e}"
                )
                raise UnknownDataBaseException from e

        logger.info(f"New instance of {self.model.get_tablename()} created")
        self.session.refresh(obj)
        return obj

    def _update(
        self,
        id: int,
        update_kwargs: dict[_DMLColumnArgument, Any],
    ) -> bool:
        """Update model instance with given kwargs.

        Args:
            - `id`: model instance id to be updated.
            - `update_kwargs`: A mapping of model's attribute names (fields)
            to new values.

        Returns:
            True if model instance was updated, False otherwise.

        Raises:
            - Validation errors if `update_kwargs` are invalid
            (see `validate_model_kwargs`).
            - `ModelInstanceNotFound` if model instance with provided id
            does not exist and update operation was not performed.
            - `SQLAlchemyError` exceptions if a db error occured.
            - `UnknownDataBaseException` if an error could not be determined.
        """
        self._validate_model_kwargs(update_kwargs)

        update_query = (
            update(self.model).where(self.model.id == id).values(update_kwargs)
        )
        try:
            updated = bool(self.session.execute(update_query).rowcount)
        except Exception as e:
            if isinstance(e, SQLAlchemyError):
                logger.error(
                    f"SQLAlchemyError during {self.model} "
                    f"instance update: {e}"
                )
                raise e
            else:
                logger.error(
                    f"Unknown exception during {self.model} "
                    f"instance update: {e}"
                )
                raise UnknownDataBaseException from e

        if updated:
            self.session.commit()
            logger.info(
                f"{self.model.get_tablename()} instance "
                f"with id `{id}` updated"
            )
        else:
            logger.info(
                f"{self.model.get_tablename()} instance"
                f"with id `{id}` not found."
            )
            raise ModelInstanceNotFound(
                f"Model {self.model.get_tablename()}, id {id}"
            )
        return updated

    def _delete(
        self,
        id: int,
    ) -> bool:
        """Delete model instance.

        Args:
            -`id`: model instance id to be deleted.

        Returns:
            True if model instance was deleted, False otherwise.

        Raises:
            - Validation errors if `update_kwargs` are invalid
            (see `validate_model_kwargs`).
            - `ModelInstanceNotFound` if model instance with provided id
            does not exist and delete operation was not performed.
            - `SQLAlchemyError` exceptions if a db error occured.
            - `UnknownDataBaseException` if an error could not be determined.
        """
        delete_query = delete(self.model).where(self.model.id == id)
        try:
            deleted = bool(self.session.execute(delete_query).rowcount)
        except Exception as e:
            if isinstance(e, SQLAlchemyError):
                logger.error(
                    f"SQLAlchemyError during {self.model} "
                    f"instance delete: {e}"
                )
                raise e
            else:
                logger.error(
                    f"Unknown exception during {self.model} "
                    f"instance delete: {e}"
                )
                raise UnknownDataBaseException from e

        if deleted:
            logger.info(
                f"{self.model.get_tablename()} instance "
                f"with id `{id}` deleted"
            )
        else:
            logger.info(
                f"{self.model.get_tablename()} instance "
                f"with id `{id}` not found."
            )
            raise ModelInstanceNotFound(
                f"Model {self.model.get_tablename()}, id {id}"
            )
        self.session.commit()
        return deleted

    def _fetch(
        self,
        query_arg: Optional[_TypedColumnClauseArgument] = None,
        *,
        order_by: Optional[List[_OrderByValue]] = None,
        filters: List[BinaryExpression] | None = None,
        join_filters: Optional[bool] = True,
    ) -> Select[Row]:
        """Construct basic SELECT query.

        This method powers other select methods in this class.

        Args:
            - `query_arg`: Object that must be queried.
                It may be a model, a column or an aggregate function.
                Defaults to None.
            - `order_by`: Sequence of objects that form the ordering of result,
                such as model.name or model.id.desc(). Defaults to None.
            - `filters`: Sequence of sqlalchemy expressions,
                such as `model.id > 1` or `model.name == 'name'`.
                Defaults to None.
            - `join_filters`: Flag that indicates whether to gather
                filter expressions by `and` or `or` clauses.
                Defaults to True.

        Returns:
            sqlalchemy.Select object that must be executed to produce result.
        """
        if query_arg is None:
            query_arg = self.model

        query = select(query_arg)

        if order_by:
            query = query.order_by(*order_by)

        if filters:
            filter_strategy = (
                partial(and_, True) if join_filters else partial(or_, False)
            )
            query = query.where(filter_strategy(*filters))

        return query

    @query_logger
    def _get(
        self,
        filters: List[BinaryExpression],
        join_filters: Optional[bool] = True,
    ) -> _BaseModel | None:
        """Get model instance.

        Args:
            - `filters`: Sequence of sqlalchemy expressions,
                such as `model.id > 1` or `model.name == 'name'`.
                Defaults to None.
            - `join_filters`: Flag that indicates whether to gather
                filter expressions by `and` or `or` clauses.
                Defaults to True..

        Returns:
            The model instance itself, if it exsists. None otherwise.
        """
        q = self._fetch(filters=filters, join_filters=join_filters)
        return self.session.execute(q).scalar_one_or_none()

    @query_logger
    def _get_many(
        self,
        *,
        order_by: Optional[List[_OrderByValue]] = None,
        filters: List[BinaryExpression] | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> ScalarResult[_BaseModel]:
        """Get several model instances.

        Args:
            - `order_by`: Sequence of objects that form the ordering of result,
                such as model.name or model.id.desc(). Defaults to None.
            - `filters`: Sequence of sqlalchemy expressions,
                such as `model.id > 1` or `model.name == 'name'`.
                Defaults to None.
            - `offset`: How many rows to skip. Defaults to 0.
            - `limit`: The max size of the query result. Defaults to 10.

        Returns:
            sqlalchemy ScalarResult iterator containing model instances.
        """
        q = self._fetch(order_by=order_by, filters=filters).limit(limit)
        if offset:
            q = q.offset(offset)

        return self.session.scalars(q)

    @query_logger
    def _count(
        self,
        filters: List[BinaryExpression] | None = None,
        join_filters: bool = True,
    ) -> int:
        """Count model items that satisfy provided filters.

        Args:
            - `filters`: Sequence of sqlalchemy expressions,
                such as `model.id > 1` or `model.name == 'name'`.
                Defaults to None.
            - `join_filters`: Flag that indicates whether to gather
                filter expressions by `and` or `or` clauses.
                Defaults to True.

        Returns:
            Number of model items.
        """
        q = self._fetch(
            func.count(self.model.id),
            filters=filters,
            join_filters=join_filters,
        )
        return self.session.scalar(q)

    @query_logger
    def _exists(
        self,
        filters: List[BinaryExpression] | None = None,
        join_filters: bool = True,
    ) -> bool:
        """Test if a model instance exists.

        Args:
            - `filters`: Sequence of sqlalchemy expressions,
                such as `model.id > 1` or `model.name == 'name'`.
                Defaults to None.
            - `join_filters`: Flag that indicates whether to gather
                filter expressions by `and` or `or` clauses.
                Defaults to True.

        Returns:
            The result of the test.
        """
        q = self._fetch(
            self.model.id,
            filters=filters,
            join_filters=join_filters,
        ).limit(1)
        return bool(self.session.scalar(q))

    def _validate(self) -> None:
        """
        Validate repository arguments.

        Returns:
            None.

        Raises:
            RepositoryValidationError if:
            - `self.session` is not an active SQLAlchemy session.
            - `self.model` is an object instead of a class.
            - `self.model` is not a subclass of `AbstractBaseModel`.
        """
        if not isinstance(self.session, (Session, scoped_session)):
            raise RepositoryValidationError(
                "Expected `self.session` to be an instance "
                "of Session or scoped_session, recieved "
                f"`{type(self.session)}`."
            )
        if not self.session.is_active:
            raise RepositoryValidationError("`self.session` is not active!")
        if not isinstance(self.model, type):
            raise RepositoryValidationError(
                "Expected `self.model` to be a class not instance. "
                f"Recieved: {self.model}"
            )
        if not issubclass(self.model, AbstractBaseModel):
            raise RepositoryValidationError(
                "Expected `self.model` to be a subclass f AbstractBaseModel, "
                f"recieved `{self.model}`."
            )

    def _validate_model_kwargs(self, kwargs: dict[str, Any]) -> None:
        """
        Validate kwargs against model fields.

        Args:
            -`kwargs`: A mapping of model's attribute names (fields)
            to values.

        Returns:
            None.

        Raises:
            - `EmptyModelKwargs` if kwargs is empty.
            - `InvalidModelAttribute` if any of kwargs keys is not
            a model's field.
            - `InvalidModelArgType` if type of any of kwargs values
            does not match model's field type.
        """
        if not kwargs:
            logger.error(
                f"Empty kwargs for model: {self.model.get_tablename()}"
            )
            raise EmptyModelKwargs(f"{self.model.get_tablename()}")

        for arg, value in kwargs.items():
            field = self.model.fields.get(arg)
            if field is None:
                logger.error(
                    "Invalid attribute for model "
                    f"{self.model.get_tablename()}: `{arg}`."
                )
                raise InvalidModelAttribute(model=self.model, invalid_arg=arg)

            if not hasattr(field, "type"):
                continue  # protect from relationships; need to raise error?

            value_type, field_type = type(value), field.type.python_type
            if not issubclass(value_type, field_type):
                logger.error(
                    f"Invalid type for `{arg}` argument: recieved "
                    f"{value_type}, instead of {field_type}"
                )
                raise InvalidModelArgType(
                    model=self.model,
                    field=field,
                    expected_type=field_type,
                    invalid_type=value_type,
                )


@dataclass
class UserRepository(CommonRepository):
    """Concrete implementation of CommonRepository
    with methods specific to User model.

    Attributes:
        - `session`: An instance of `sqlalchemy.orm.Session`
        or `scoped_session`; session's `is_active` property must return True.
    """

    model: Type[_BaseModel] = field(default=User, init=False)

    def get_user(self, *, user_id: int = 0, tg_id: int = 0) -> User | None:
        return self._get(
            filters=[self.model.id == user_id, self.model.tg_id == tg_id],
            join_filters=False,
        )

    def create_user(
        self,
        tg_id: int,
        budget_currency: str,
    ) -> User:
        return self._create(tg_id=tg_id, budget_currency=budget_currency)

    def update_user(
        self,
        user_id: int,
        *,
        budget_currency: str = None,
        is_active: bool = None,
    ) -> bool:
        return self._update(user_id, get_locals(locals(), ("self", "user_id")))

    def delete_user(
        self,
        user_id: int,
    ) -> bool:
        return self._delete(user_id)

    def count_users(
        self,
        filters: List[BinaryExpression] | None = None,
        join_filters: bool = True,
    ) -> int:
        return self._count(filters, join_filters)

    def user_exists(self, *, user_id: int = 0, tg_id: int = 0) -> bool:
        return self._exists(
            [
                self.model.id == user_id,
                self.model.tg_id == tg_id,
            ],
            join_filters=False,
        )


@dataclass
class CategoryRepository(CommonRepository):
    """Concrete implementation of CommonRepository
    with methods specific to Category model.

    Attributes:
        - `session`: An instance of `sqlalchemy.orm.Session`
        or `scoped_session`; session's `is_active` property must return True.
    """

    model: Type[_BaseModel] = field(default=Category, init=False)

    def get_category(
        self,
        category_id: int,
    ) -> Category | None:
        return self._get(filters=[self.model.id == category_id])

    @attributed_result
    def get_user_categories(
        self, user_id: int, *, offset: int = 0, limit: int = 5
    ) -> GeneratorResult:
        return self._get_many(
            order_by=[
                self.model.last_used.desc(),
                self.model.created_at.desc(),
            ],
            filters=[self.model.user_id == user_id],
            offset=offset,
            limit=limit,
        )

    def create_category(
        self,
        user_id: int,
        name: str,
        type: CategoryType,
    ) -> Category:
        return self._create(
            user_id=user_id,
            name=name,
            type=type,
        )

    def update_category(
        self,
        category_id: int,
        *,
        name: str = None,
        type: CategoryType = None,
        last_used: datetime = None,
        num_entries: int = None,
    ) -> bool:
        return self._update(
            category_id, get_locals(locals(), ("self", "category_id"))
        )

    def delete_category(
        self,
        category_id: int,
    ) -> bool:
        return self._delete(category_id)

    def count_user_categories(self, user_id: int) -> int:
        return self._count([self.model.user_id == user_id])

    def category_exists(
        self,
        *,
        category_id: int = 0,
        user_id: int = 0,
        category_name: str = None,
    ) -> bool:
        filters = [
            self.model.id == category_id,
            self.model.user_id == user_id,
        ]
        join_filters = False

        if category_name is not None:
            filters = [
                self.model.name == category_name,
                self.model.user_id == user_id,
            ]
            join_filters = True

        return self._exists(filters, join_filters)

    def count_category_entries(self, category_id: int) -> int:
        return self.session.scalar(
            self._fetch(
                func.count(Entry.id),
                filters=[Entry.category_id == category_id],
            )
        )


@dataclass
class EntryRepository(CommonRepository):
    """Concrete implementation of CommonRepository
    with methods specific to Entry model.

    Attributes:
        - `session`: An instance of `sqlalchemy.orm.Session`
        or `scoped_session`; session's `is_active` property must return True.
    """

    model: Type[_BaseModel] = field(default=Entry, init=False)

    def get_entry(self, entry_id: int) -> Entry | None:
        q = self._fetch(filters=[self.model.id == entry_id]).options(
            joinedload(self.model.user), joinedload(self.model.category)
        )
        return self.session.execute(q).scalar_one_or_none()

    def create_entry(
        self,
        user_id: int,
        category_id: int,
        sum: int,
        transaction_date: Optional[datetime] = None,
        description: Optional[str] = None,
    ) -> Entry:
        create_kwargs = {
            "user_id": user_id,
            "category_id": category_id,
            "sum": sum,
        }
        if transaction_date is not None:
            create_kwargs["transaction_date"] = transaction_date

        if description is not None:
            create_kwargs["description"] = description

        return self._create(**create_kwargs)

    def update_entry(
        self,
        entry_id,
        *,
        sum: int = None,
        transaction_date: datetime = None,
        description: str = None,
        category_id: int = None,
    ) -> bool:
        return self._update(
            entry_id, get_locals(locals(), ("self", "entry_id"))
        )

    def delete_entry(
        self,
        entry_id: int,
    ) -> bool:
        return self._delete(entry_id)

    def count_entries(self, *, user_id: int = 0, category_id: int = 0) -> bool:
        return self._count(
            filters=[
                self.model.user_id == user_id,
                self.model.category_id == category_id,
            ],
            join_filters=False,
        )

    def entry_exists(
        self, *, entry_id: int = 0, user_id: int = 0, category_id: int = 0
    ) -> bool:
        return self._exists(
            filters=[
                self.model.id == entry_id,
                self.model.user_id == user_id,
                self.model.category_id == category_id,
            ],
            join_filters=False,
        )


def get_user(
    db_session: Session | scoped_session, *, user_id: int = 0, tg_id: int = 0
) -> User | None:
    if not (user_id or tg_id):
        raise ValueError(
            "Provide either a `user_id` or `tg_id` argument for get_user."
        )

    return UserRepository(db_session).get_user(user_id=user_id, tg_id=tg_id)
