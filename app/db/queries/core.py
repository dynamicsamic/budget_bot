import datetime as dt
import logging
from collections import namedtuple
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Generator, List, Optional, Tuple, Type

from sqlalchemy import and_
from sqlalchemy import delete as sql_delete
from sqlalchemy import func, or_, select
from sqlalchemy import update as sql_update
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.engine.row import Row
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Query,
    Session,
    scoped_session,
)
from sqlalchemy.sql._typing import (
    _DMLColumnArgument,
    _TypedColumnClauseArgument,
)
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.sql.selectable import Select

from app.db import models
from app.db.custom_types import _BaseModel, _ModelWithDatefield, _OrderByValue

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


def fetch(
    model: Type[_BaseModel],
    session: Session | scoped_session,
    *,
    order_by: Optional[List[_OrderByValue]] = None,
    filters: Optional[List[BinaryExpression]] = None,
) -> Query[_BaseModel]:
    """Basic SELECT query with optional ordering and filtering.

    This is the underlying query for almost all SELECT functions
    that are part of this package's public API.

    Args:
        model: A subclass of app.models.base.AbstractBaseModel.
        session: An instance of sqlalchemy.orm.Session or scoped_session.
        order_by: A list model attributes or unary expressions on it.
        filters: A list of binary expressions on model attributes.

    Returns:
        sqlalchemy.Query that will produce a list of selected model objects
            when invoking the all() method.

    Examples:
        ```
        _fetch(Entry, db_session)
        ```
        produces SELECT * FROM entry

        ```
        _fetch(Entry, db_session, order_by=[-Entry.id], filters=[Entry.sum > 0])
        ```
        produces SELECT ... FROM entry WHERE entry.sum > 0 ORDER BY -entry.id
    """
    query = session.query(model)

    if order_by is not None:
        query = query.order_by(*order_by)

    if filters is not None:
        query = query.filter(and_(True, *filters))

    return query


def aggregate_fetch(
    session: Session | scoped_session,
    aggregate_function: GenericFunction,
    target_column: InstrumentedAttribute,
    filters: Optional[List[BinaryExpression]] = None,
) -> Any:
    query = session.query(aggregate_function(target_column))

    if filters is not None:
        query = query.filter(and_(True, *filters))

    return query.scalar()


def between(
    model: Type[_ModelWithDatefield],
    session: Session | scoped_session,
    start: dt.datetime | dt.date,
    end: dt.datetime | dt.date,
    order_by: Optional[List[_OrderByValue]] = None,
    filters: Optional[List[BinaryExpression]] = None,
) -> Query[_ModelWithDatefield]:
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
    filters = filters or []
    filters.append(model._datefield.between(start, end))
    return fetch(model, session, order_by=order_by, filters=filters)


def aggregate_between(
    model: Type[_ModelWithDatefield],
    session: Session | scoped_session,
    start: dt.datetime | dt.date,
    end: dt.datetime | dt.date,
    aggregate_function: GenericFunction,
    target_column: InstrumentedAttribute,
    filters: Optional[List[BinaryExpression]] = None,
) -> Query[_ModelWithDatefield]:
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
    filters = filters or []
    filters.append(model._datefield.between(start, end))
    return aggregate_fetch(
        session, aggregate_function, target_column, filters=filters
    )


@dataclass
class DbSessionController:
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

            # updated = bool(
            #     self.session.query(self.model).filter_by(id=id).update(update_kwargs)
            # )
        update_query = (
            sql_update(self.model)
            .where(self.model.id == id)
            .values(update_kwargs)
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
        # deleted = bool(session.query(model).filter_by(id=id).delete())
        # session.commit()
        delete_query = sql_delete(self.model).where(self.model.id == id)
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
class UserModelController(DbSessionController):
    model: Type[_BaseModel] = field(default=models.User, init=False)

    def get_user(self, user_id: int = 0, tg_id: int = 0) -> models.User | None:
        return self._get(
            filters=[self.model.id == user_id, self.model.tg_id == tg_id],
            join_filters=False,
        )

    def create_user(
        self,
        tg_id: int,
    ) -> models.User | None:
        return self._create(tg_id=tg_id)

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
class BudgetModelController(DbSessionController):
    model: Type[_BaseModel] = field(default=models.Budget, init=False)

    def get_budget(self, budget_id: int) -> models.Budget | None:
        return self._get(
            filters=[self.model.id == budget_id],
        )

    @attributed_result
    def get_user_budgets(
        self, user_id: int, offset: int = 0, limit: int = 5
    ) -> AttributedResult[bool, models.Budget, Generator]:
        return self._get_all(
            order_by=[self.model.created_at.desc()],
            filters=[self.model.user_id == user_id],
            offset=offset,
            limit=limit,
        )

    def create_budget(
        self,
        user_id: int,
        name: str,
        currency: str,
    ) -> models.User | None:
        return self._create(user_id=user_id, name=name, currency=currency)

    def update_budget(
        self,
        budget_id: int,
        update_kwargs: dict[_DMLColumnArgument, Any],
    ) -> bool:
        return self._update(budget_id, update_kwargs)

    def delete_budget(
        self,
        budget_id: int,
    ) -> bool:
        return self._delete(budget_id)

    def count_user_budgets(self, user_id: int) -> int:
        return self._count([self.model.user_id == user_id])

    def budget_exists(
        self, *, budget_id: int = 0, budget_name: str = "", user_id: int = 0
    ) -> bool:
        return self._exists(
            [
                self.model.id == budget_id,
                self.model.name == budget_name,
                self.model.user_id == user_id,
            ],
            join_filters=False,
        )


@dataclass
class EntryCategoryModelController(DbSessionController):
    model: Type[_BaseModel] = field(default=models.EntryCategory, init=False)

    def get_category(
        self,
        entry_category_id: int,
    ) -> models.EntryCategory:
        return self._get(
            filters=[self.model.id == entry_category_id],
        )

    @attributed_result
    def get_budget_categories(
        self, budget_id: int, offset: int = 0, limit: int = 5
    ) -> ScalarResult[models.EntryCategory]:
        return self._get_all(
            order_by=[
                self.model.last_used.desc(),
                self.model.created_at.desc(),
            ],
            filters=[self.model.budget_id == budget_id],
            offset=offset,
            limit=limit,
        )

    def create_entry_category(
        self,
        budget_id: int,
        name: str,
        type: models.EntryType,
    ) -> models.EntryCategory | None:
        return self._create(
            budget_id=budget_id,
            name=name,
            type=type,
        )

    def update_entry_category(
        self,
        entry_category_id: int,
        update_kwargs: dict[_DMLColumnArgument, Any],
    ) -> bool:
        return self._update(entry_category_id, update_kwargs)

    def delete_entry_category(
        self,
        entry_category_id: int,
    ) -> bool:
        return self._delete(entry_category_id)

    def count_budget_categories(self, budget_id: int) -> int:
        return self._count([self.budget_id == budget_id])

    def entry_category_exists(
        self,
        *,
        entry_category_id: int = 0,
        budget_id: int = 0,
        search_by_category_name_args: Tuple[str, int] = None,
    ) -> bool:
        if search_by_category_name_args:
            name, budget_id = search_by_category_name_args
            return self._exists(
                [self.model.name == name, self.model.budget_id == budget_id]
            )

        return self._exists(
            [
                self.model.id == entry_category_id,
                self.model.budget_id == budget_id,
            ],
            join_filters=False,
        )


user_controller = UserModelController
budget_controller = BudgetModelController
category_controller = EntryCategoryModelController
