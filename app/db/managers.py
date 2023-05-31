from typing import Any, Type

from sqlalchemy import func, select, text
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.orm import Session

from app import settings
from app.utils import session_agnostic

from . import prod_engine, test_engine
from .base import BaseModel


class QueryManager:
    def __init__(self, model: Type[BaseModel]) -> None:
        self.model = model
        self.db_engine = test_engine if settings.DEBUG else prod_engine

    @session_agnostic
    def count(self, session: Session = None) -> int:
        """Return number of all instances in the DB."""
        query = select(func.count(self.model.id))
        return session.scalar(query)

    @session_agnostic
    def all(
        self, session: Session = None, to_list: bool = False
    ) -> ScalarResult[Type[BaseModel]] | list[Type[BaseModel]]:
        """Return all instances either in list or in ScalarResult."""
        qs = session.scalars(select(self.model))
        return qs.all() if to_list else qs

    @session_agnostic
    def get(
        self, value: Any, session: Session = None, search_field: str = None
    ):
        if search_field is not None and hasattr(self.model, search_field):
            print("HEHEH")
            search_query = f"{self.model.__name__}.{search_field}==name1"
            return session.scalar(
                select(self.model)
                .filter(text(f"{search_field}=:value"))
                .params(value=value)
            )

        primary_keys = [
            attr_name
            for attr_name, attr in self.model.__dict__.items()
            if not attr_name.startswith("_")
            and hasattr(attr, "primary_key")
            and getattr(attr, "primary_key")
        ]
        if search_field is None and primary_keys:
            return session.get(self.model, {primary_keys[0]: value})
