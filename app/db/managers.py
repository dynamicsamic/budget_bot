from typing import Any, Type

from sqlalchemy import func, select, text
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import QueryableAttribute

from app import settings
from app.utils import session_agnostic

from . import prod_engine, test_engine
from .base import BaseModel


class QueryManager:
    def __init__(self, model: Type[BaseModel]) -> None:
        self.model = model
        self.db_engine = test_engine if settings.DEBUG else prod_engine

    @property
    def model_fields(self) -> dict[str, Type[QueryableAttribute]]:
        return {
            attr_name: attr_obj
            for attr_name, attr_obj in self.model.__dict__.items()
            if not attr_name.startswith("_")
            and hasattr(attr_obj, "primary_key")
        }

    @property
    def model_fieldnames(self) -> list[str]:
        return list(self.model_fields.keys())

    @property
    def model_fieldtypes(self) -> list[str]:
        return [field.type for field in self.model_fields.values()]

    @property
    def model_primary_keys(self) -> list[str]:
        return [
            fieldname
            for fieldname, field_obj in self.model_fields.items()
            if getattr(field_obj, "primary_key")
        ]

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
        pk_value: Any = None,
        *,
        session: Session = None,
        **kwargs,
    ) -> Type[BaseModel] | None:
        """Return one instance of `self.model`."""
        if pk_value:
            if pk := self.model_primary_keys[0]:
                return session.get(self.model, {pk: pk_value})
            # maybe need to raise error in else clause

        elif kwargs:
            attr, pk_value = list(kwargs.items())[0]
            try:
                return session.scalar(
                    select(self.model)
                    .filter(text(f"{attr}=:value"))
                    .params(value=pk_value)
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
