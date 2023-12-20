import logging
from collections import namedtuple
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Generator, List, Optional, Type

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.engine.row import Row
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.sql._typing import (
    _DMLColumnArgument,
    _TypedColumnClauseArgument,
)
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.selectable import Select

from app.db.custom_types import _BaseModel, _OrderByValue
from app.db.models import Category, CategoryType, User

logger = logging.getLogger(__name__)


def validate_model_kwargs(model: _BaseModel, kwargs: dict[str, Any]) -> bool:
    model_fields = model.fields

    for arg, value in kwargs.items():
        field = model_fields.get(arg)
        if field is None:
            logger.error(
                "Invalid attribute for model "
                f"{model.__tablename__.capitalize()}: `{arg}`."
            )
            return False

        value_type, field_type = type(value), field.type.python_type
        if not issubclass(value_type, field_type):
            logger.error(
                f"Invalid type for `{arg}` argument: recieved "
                f"{value_type}, instead of {field_type}"
            )
            return False

    return True


def linked_generator(
    head: _BaseModel, tail: ScalarResult[_BaseModel]
) -> Generator[_BaseModel, None, None]:
    yield head
    for i in tail:
        yield i


AttributedResult = namedtuple(
    "AttributedResult", ["is_empty", "head", "result"]
)


def attributed_result(f):
    def wrapped(*args, **kwargs) -> AttributedResult:
        res: ScalarResult = f(*args, **kwargs)
        try:
            head = next(res)
        except StopIteration:
            return AttributedResult(True, None, [])
        return AttributedResult(False, head, linked_generator(head, res))

    return wrapped


@dataclass
class CommonRepository:
    session: Session | scoped_session
    model: Type[_BaseModel]

    def _create(
        self,
        **create_kwargs: Any,
    ) -> _BaseModel | None:
        """Create an instance of model.

        Args:
            model: A subclass of app.models.base.AbstractBaseModel.
            session: An instance of sqlalchemy.orm.Session or scoped_session.
            create_kwargs: A mapping of model's attribute (field) names
            to their values.

        Returns:
            The newly created instance or None if error occured.
        """
        if not validate_model_kwargs(self.model, create_kwargs):
            return

        obj = self.model(**create_kwargs)
        try:
            self.session.add(obj)
            self.session.commit()
        except Exception as e:
            logger.error(f"Instance creation [FAILURE]: {e}")
            return
        logger.info(f"New instance of {self.model} created")
        return obj

    def _update(
        self,
        id: int,
        update_kwargs: dict[_DMLColumnArgument, Any],
    ) -> bool:
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
        if not validate_model_kwargs(self.model, update_kwargs):
            return False

        update_query = (
            update(self.model).where(self.model.id == id).values(update_kwargs)
        )
        try:
            updated = bool(self.session.execute(update_query).rowcount)
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
                f"with id `{id}` update [SUCCESS]"
            )
        else:
            logger.info(
                f"No instance of {self.model.__tablename__.upper()} "
                f"with id `{id}` found."
            )
        return updated

    def _delete(
        self,
        id: int,
    ) -> bool:
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
                f"{self.model.__tablename__.upper()} "
                f"instance delete [FAILURE]: {e}"
            )
            return False
        if deleted:
            logger.info(
                f"{self.model.__tablename__.upper()} instance "
                f"with id `{id}` delete [SUCCESS]"
            )
        else:
            logger.warning(
                f"Attempt to delete instance of "
                f"{self.model.__tablename__.upper()} with id `{id}`. "
                "No delete performed."
            )
        return deleted

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

    def _get(
        self,
        filters: List[BinaryExpression],
        join_filters: Optional[bool] = True,
    ) -> _BaseModel | None:
        q = self._fetch(filters=filters, join_filters=join_filters)
        return self.session.execute(q).scalar_one_or_none()

    def _get_all(
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

    def _count(
        self,
        filters: Optional[List[BinaryExpression]] = None,
        join_filters: Optional[bool] = True,
    ) -> int:
        q = self._fetch(
            func.count(self.model.id),
            filters=filters,
            join_filters=join_filters,
        )
        return self.session.scalar(q)

    def _exists(
        self,
        filters: Optional[List[BinaryExpression]] = None,
        join_filters: Optional[bool] = True,
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

    def get_user(self, user_id: int = 0, tg_id: int = 0) -> User | None:
        return self._get(
            filters=[self.model.id == user_id, self.model.tg_id == tg_id],
            join_filters=False,
        )

    def create_user(
        self,
        tg_id: int,
        budget_currency: str,
    ) -> User | None:
        return self._create(tg_id=tg_id, budget_currency=budget_currency)

    def update_user(self, user_id: int, is_active: bool) -> bool:
        return self._update(user_id, {"is_active": is_active})

    def delete_user(
        self,
        user_id: int,
    ) -> bool:
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
        entry_category_id: int,
    ) -> Category:
        return self._get(
            filters=[self.model.id == entry_category_id],
        )

    @attributed_result
    def get_user_categories(
        self, user_id: int, offset: int = 0, limit: int = 5
    ) -> AttributedResult[bool, Category, Generator]:
        return self._get_all(
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
    ) -> Category | None:
        return self._create(
            user_id=user_id,
            name=name,
            type=type,
        )

    def update_category(
        self,
        category_id: int,
        update_kwargs: dict[_DMLColumnArgument, Any],
    ) -> bool:
        return self._update(category_id, update_kwargs)

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
