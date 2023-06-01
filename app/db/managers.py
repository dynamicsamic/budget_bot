from typing import Any, Type

from sqlalchemy import func, select, text
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.exc import SQLAlchemyError
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
        self,
        value: Any = None,
        *,
        session: Session = None,
        **kwargs,
    ) -> Type[BaseModel] | None:
        """Return one instance of `self.model`."""
        if value:
            if primary_keys := [
                attr_name
                for attr_name, attr in self.model.__dict__.items()
                if not attr_name.startswith("_")
                and hasattr(attr, "primary_key")
                and getattr(attr, "primary_key")
            ]:
                return session.get(self.model, {primary_keys[0]: value})
            # maybe need to raise error in else clause

        elif kwargs:
            attr, value = list(kwargs.items())[0]
            try:
                return session.scalar(
                    select(self.model)
                    .filter(text(f"{attr}=:value"))
                    .params(value=value)
                )
            except SQLAlchemyError:
                return

    @session_agnostic
    def filter(
        self,
        session: Session = None,
        to_list: bool = False,
        **kwargs,
    ) -> ScalarResult[Type[BaseModel]] | list[Type[BaseModel]]:
        """Return queryset of `self.model` instances
        either in list or in ScalarResult.
        """
        text_ = " and ".join(
            (
                f"{search_field}=:val{i}"
                for i, search_field in enumerate(kwargs.keys())
            )
        )
        params_ = {f"val{i}": value for i, value in enumerate(kwargs.values())}
        try:
            qs = session.scalars(
                select(self.model).filter(text(text_)).params(params_)
            )
        except SQLAlchemyError:
            return

        return qs.all() if to_list else qs
