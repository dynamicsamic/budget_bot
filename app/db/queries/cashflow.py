import logging
from typing import List, Optional, Type

from sqlalchemy import and_
from sqlalchemy import func as sql_func
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import BinaryExpression

from app.db.custom_types import _ModelWithCashflowfield

logger = logging.getLogger(__name__)


def generate_summed_query(
    model: Type[_ModelWithCashflowfield],
    query: Query,
    filters: Optional[List[BinaryExpression]] = None,
) -> int:
    if filters:
        query = query.filter(and_(True, *filters))

    return (
        query.with_entities(sql_func.sum(model._cashflowfield)).scalar() or 0
    )
