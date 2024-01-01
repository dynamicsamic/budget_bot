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

from app.utils import get_locals

from .custom_types import (
    GeneratorResult,
    ModelCreateResult,
    ModelUpdateDeleteResult,
    ModelValidationResult,
    _BaseModel,
    _OrderByValue,
)
from .exceptions import (
    EmptyModelKwargs,
    InvalidModelArgType,
    InvalidModelArgValue,
    ModelInstanceNotFound,
)
from .models import Category, CategoryType, Entry, User

logger = logging.getLogger(__name__)


def validate_model_kwargs(
    model: _BaseModel, kwargs: dict[str, Any]
) -> ModelValidationResult:
    if not kwargs:
        logger.error(f"Empty kwargs for model: {model.get_tablename()}")
        return ModelValidationResult(
            result=False, error=EmptyModelKwargs(f"{model.get_tablename()}")
        )

    model_fields = model.fields

    for arg, value in kwargs.items():
        field = model_fields.get(arg)
        if field is None:
            logger.error(
                "Invalid attribute for model "
                f"{model.get_tablename()}: `{arg}`."
            )
            return ModelValidationResult(
                result=False,
                error=InvalidModelArgValue(model=model, invalid_arg=arg),
            )

        value_type, field_type = type(value), field.type.python_type
        if not issubclass(value_type, field_type):
            logger.error(
                f"Invalid type for `{arg}` argument: recieved "
                f"{value_type}, instead of {field_type}"
            )
            return ModelValidationResult(
                result=False,
                error=InvalidModelArgType(
                    model=model,
                    arg_name=arg,
                    expected_type=field_type,
                    invalid_type=value_type,
                ),
            )

    return ModelValidationResult(result=True, error=None)


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
    session: Session | scoped_session
    model: Type[_BaseModel]

    def _create(
        self,
        **create_kwargs: Any,
    ) -> ModelCreateResult:
        """Create an instance of model.

        Args:
            model: A subclass of app.models.base.AbstractBaseModel.
            session: An instance of sqlalchemy.orm.Session or scoped_session.
            create_kwargs: A mapping of model's attribute (field) names
            to their values.

        Returns:
            The newly created instance or None if error occured.
        """
        validated, error = validate_model_kwargs(
            self.model, create_kwargs
        ).astuple()

        if not validated:
            return ModelCreateResult(result=None, error=error)

        obj = self.model(**create_kwargs)
        try:
            self.session.add(obj)
            self.session.commit()
        except Exception as e:
            logger.error(f"Instance creation [FAILURE]: {e}")
            return ModelCreateResult(result=None, error=e)

        logger.info(f"New instance of {self.model} created")
        self.session.refresh(obj)
        return ModelCreateResult(result=obj, error=None)

    def _update(
        self,
        id: int,
        update_kwargs: dict[_DMLColumnArgument, Any],
    ) -> ModelUpdateDeleteResult:
        """Update model instance with given kwargs.

        Args:
            model: A subclass of app.models.base.AbstractBaseModel.
            session: An instance of sqlalchemy.orm.Session or scoped_session.
            id: id of the model instance to be updated.
            update_kwargs: A mapping of model's attribute names (fields) that
                should be updated to new values.

        Returns:
            True if update performed successfully, False otherwise.
        """
        validated, error = validate_model_kwargs(
            self.model, update_kwargs
        ).astuple()

        if not validated:
            return ModelUpdateDeleteResult(result=None, error=error)

        update_query = (
            update(self.model).where(self.model.id == id).values(update_kwargs)
        )
        try:
            updated = bool(self.session.execute(update_query).rowcount)
        except Exception as e:
            logger.error(
                f"{self.model.get_tablename()} "
                f"instance update [FAILURE]: {e}"
            )
            return ModelUpdateDeleteResult(result=None, error=e)
        if updated:
            self.session.commit()
            logger.info(
                f"{self.model.get_tablename()} instance "
                f"with id `{id}` update [SUCCESS]"
            )
            return ModelUpdateDeleteResult(result=True, error=None)
        else:
            logger.info(
                f"No instance of {self.model.get_tablename()} "
                f"with id `{id}` found."
            )
            return ModelUpdateDeleteResult(
                result=False,
                error=ModelInstanceNotFound(
                    "Записи с такими данными не существует"
                ),
            )

    def _delete(
        self,
        id: int,
    ) -> ModelUpdateDeleteResult:
        """Delete `self.model` instance with given id.

        Args:
            model: A subclass of app.models.base.AbstractBaseModel.
            session: An instance of sqlalchemy.orm.Session or scoped_session.
            id: id of the model instance to be updated.

        Returns:
            True if delete performed successfully, False otherwise.
        """
        delete_query = delete(self.model).where(self.model.id == id)
        try:
            deleted = bool(self.session.execute(delete_query).rowcount)
        except SQLAlchemyError as e:
            logger.error(
                f"{self.model.get_tablename()} "
                f"instance delete [FAILURE]: {e}"
            )
            return ModelUpdateDeleteResult(result=None, error=e)
        if deleted:
            logger.info(
                f"{self.model.get_tablename()} instance "
                f"with id `{id}` delete [SUCCESS]"
            )
            return ModelUpdateDeleteResult(result=True, error=None)
        else:
            logger.warning(
                f"Attempt to delete instance of "
                f"{self.model.get_tablename()} with id `{id}`. "
                "No delete performed."
            )
            return ModelUpdateDeleteResult(
                result=False,
                error=ModelInstanceNotFound(
                    "Записи с такими данными не существует"
                ),
            )

    def _fetch(
        self,
        query_arg: Optional[_TypedColumnClauseArgument] = None,
        *,
        order_by: Optional[List[_OrderByValue]] = None,
        filters: Optional[List[BinaryExpression]] = None,
        join_filters: Optional[bool] = True,
    ) -> Select[Row]:
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
        q = self._fetch(filters=filters, join_filters=join_filters)
        return self.session.execute(q).scalar_one_or_none()

    @query_logger
    def _get_many(
        self,
        *,
        order_by: Optional[List[_OrderByValue]] = None,
        filters: Optional[List[BinaryExpression]] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> ScalarResult[_BaseModel]:
        q = self._fetch(order_by=order_by, filters=filters).limit(limit)
        if offset:
            q = q.offset(offset)

        return self.session.scalars(q)

    @query_logger
    def _count(
        self,
        filters: Optional[List[BinaryExpression]] = None,
        join_filters: bool = True,
    ) -> int:
        q = self._fetch(
            func.count(self.model.id),
            filters=filters,
            join_filters=join_filters,
        )
        return self.session.scalar(q)

    @query_logger
    def _exists(
        self,
        filters: Optional[List[BinaryExpression]] = None,
        join_filters: bool = True,
    ) -> bool:
        q = self._fetch(
            self.model.id,
            filters=filters,
            join_filters=join_filters,
        ).limit(1)
        return bool(self.session.scalar(q))


@dataclass
class UserRepository(CommonRepository):
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
    ) -> ModelCreateResult:
        return self._create(tg_id=tg_id, budget_currency=budget_currency)

    def update_user(
        self,
        user_id: int,
        *,
        budget_currency: str = None,
        is_active: bool = None,
    ) -> ModelUpdateDeleteResult:
        return self._update(user_id, get_locals(locals(), ("self", "user_id")))

    def delete_user(
        self,
        user_id: int,
    ) -> ModelUpdateDeleteResult:
        return self._delete(user_id)

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
    ) -> ModelCreateResult:
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
    ) -> ModelUpdateDeleteResult:
        return self._update(
            category_id, get_locals(locals(), ("self", "category_id"))
        )

    def delete_category(
        self,
        category_id: int,
    ) -> ModelUpdateDeleteResult:
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


@dataclass
class EntryRepository(CommonRepository):
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
    ) -> ModelCreateResult:
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
    ) -> ModelUpdateDeleteResult:
        return self._update(
            entry_id, get_locals(locals(), ("self", "entry_id"))
        )

    def delete_entry(
        self,
        entry_id: int,
    ) -> ModelUpdateDeleteResult:
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
