import logging
from typing import Any, List, Optional, Type

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.sql._typing import _DMLColumnArgument
from sqlalchemy.sql.elements import BinaryExpression

from app.db.custom_types import _BaseModel, _OrderByValue

from .core import fetch
from .extra import validate_model_kwargs

logger = logging.getLogger(__name__)


def create(
    model: Type[_BaseModel],
    session: Session | scoped_session,
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
    if not validate_model_kwargs(model, create_kwargs):
        return

    obj = model(**create_kwargs)
    try:
        session.add(obj)
        session.commit()
    except Exception as e:
        logger.error(f"Instance creation [FAILURE]: {e}")
        return
    logger.info(f"New instance of {model} created")
    return obj


def update(
    model: Type[_BaseModel],
    session: Session | scoped_session,
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
    if not validate_model_kwargs(model, update_kwargs):
        return False

    try:
        updated = bool(
            session.query(model).filter_by(id=id).update(update_kwargs)
        )
    except Exception as e:
        logger.error(
            f"{model.__tablename__.upper()} " f"instance update [FAILURE]: {e}"
        )
        return False
    if updated:
        session.commit()
        logger.info(
            f"{model.__tablename__.upper()} instance "
            f"with id `{id}` update [SUCCESS]"
        )
    else:
        logger.info(
            f"No instance of {model.__tablename__.upper()} "
            f"with id `{id}` found."
        )
    return updated


def delete(
    model: Type[_BaseModel],
    session: Session | scoped_session,
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
    try:
        deleted = bool(session.query(model).filter_by(id=id).delete())
        session.commit()
    except SQLAlchemyError as e:
        logger.error(
            f"{model.__tablename__.upper()} " f"instance delete [FAILURE]: {e}"
        )
        return False
    if deleted:
        logger.info(
            f"{model.__tablename__.upper()} instance "
            f"with id `{id}` delete [SUCCESS]"
        )
    else:
        logger.warning(
            f"Attempt to delete instance of "
            f"{model.__tablename__.upper()} with id `{id}`. "
            "No delete performed."
        )
    return deleted


def get(
    model: Type[_BaseModel],
    session: Session | scoped_session,
    filters: List[BinaryExpression],
) -> _BaseModel:
    """Fetch a model instance with given id.

    Args:
        model: A subclass of app.models.base.AbstractBaseModel.
        session: An instance of sqlalchemy.orm.Session or scoped_session.
        id: id of the model instance to be found.

    Returns:
        model instance or None.
    """
    return fetch(model, session, filters=filters).one_or_none()


def get_all(
    model: Type[_BaseModel],
    session: Session | scoped_session,
    order_by: Optional[List[_OrderByValue]] = None,
    filters: Optional[List[BinaryExpression]] = None,
) -> Query[_BaseModel]:
    """Fetch all model instances that suit given filters.

    Args:
        model: A subclass of app.models.base.AbstractBaseModel.
        session: An instance of sqlalchemy.orm.Session or scoped_session.
        order_by: A list model attributes or unary expressions on it.
        filters: A list of binary expressions on model attributes.

    Returns:
        sqlalchemy.Query that will produce a list of selected model objects
            when invoking the all() method.

    """
    return fetch(model, session, order_by=order_by, filters=filters)
