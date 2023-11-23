import datetime as dt
import logging
from typing import List, Optional, Type

from sqlalchemy.orm import Query, Session, scoped_session
from sqlalchemy.sql.elements import BinaryExpression

from app.db.custom_types import _ModelWithDatefield, _OrderByValue

from .core import between

logger = logging.getLogger(__name__)


def today(
    model: Type[_ModelWithDatefield],
    session: Session | scoped_session,
    start: dt.datetime | dt.date,
    end: dt.datetime | dt.date,
    order_by: Optional[List[_OrderByValue]] = None,
    filters: Optional[List[BinaryExpression]] = None,
) -> Query[_ModelWithDatefield]:
    """Fetch model instances between the start and end of today.

    Args:
        model: A subclass of app.models.base.AbstractBaseModel.
        session: An instance of sqlalchemy.orm.Session or scoped_session.
        date_info: Instance of DateGen class.
        order_by: A list model attributes or unary expressions on it.
        filters: A list of binary expressions on model attributes.
    Returns:
        sqlclahemy.Query that contains model instances between given gaps.
    """
    return between(model, session, start, end, order_by, filters)
