import logging
from typing import Any, List, Optional, Type

from sqlalchemy import func
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.sql.elements import BinaryExpression

from app.db.custom_types import _BaseModel

from .core import aggregate_fetch

logger = logging.getLogger(__name__)


def count(
    model: Type[_BaseModel],
    session: Session | scoped_session,
    filters: Optional[List[BinaryExpression]] = None,
) -> int:
    """Calculate the number of model instances filtered by provided values.
    If no filters provided, calculate the number of all model instances.

    Args:
        model: A subclass of app.models.base.AbstractBaseModel.
        session: An instance of sqlalchemy.orm.Session or scoped_session.
        filters: A list of binary expressions on model attributes.

    Returns:
        Number of model instances.

    Examples:
        ```
        manager.count()
        ```
    or
        ```
        manager.count(filters=["model.id>100"])
        ```
    """
    return aggregate_fetch(session, func.count, model.id, filters)


def summate(
    model: Type[_BaseModel],
    session: Session | scoped_session,
    filters: Optional[List[BinaryExpression]] = None,
) -> int:
    return aggregate_fetch(session, func.sum, model._cashflowfield, filters)


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
