from dataclasses import dataclass
from typing import Any, Type

from sqlalchemy import func, select, text
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, scoped_session

from app import settings
from app.utils import session_agnostic

from . import prod_engine, test_engine
from .base import AbstractBaseModel


class QueryManager:
    def __init__(self, model: Type[AbstractBaseModel]) -> None:
        self.model = model
        self.db_engine = test_engine if settings.DEBUG else prod_engine

    @session_agnostic
    def count(self, session: Session = None) -> int:
        """Calculate number of all `self.model` objects."""
        query = select(func.count(self.model.id))
        return session.scalar(query)

    @session_agnostic
    def getall(
        self, session: Session = None, to_list: bool = False
    ) -> ScalarResult[Type[AbstractBaseModel]] | list[Type[AbstractBaseModel]]:
        """Retrieve all `self.model` objets
        either in `ScalarResult` or `list` form.
        """
        qs = session.scalars(select(self.model))
        return qs.all() if to_list else qs

    @session_agnostic
    def get(
        self,
        pk_value: Any = None,
        *,
        session: Session = None,
        **kwargs,
    ) -> Type[AbstractBaseModel] | None:
        """Retrieve `self.model` object."""
        if pk_value and (primary_keys := self.model.primary_keys):
            return session.get(self.model, {primary_keys[0]: pk_value})
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
    ) -> ScalarResult[Type[AbstractBaseModel]] | list[Type[AbstractBaseModel]]:
        """Return queryset of `self.model` instances
        either in list or in ScalarResult.
        """
        # Drop all filter params not related to self.model.
        filter_by = {
            fieldname: filter_value
            for fieldname, filter_value in kwargs.items()
            if fieldname in self.model.fieldnames
        }
        text_ = " and ".join(
            (
                f"{fieldname}=:val{i}"
                for i, fieldname in enumerate(filter_by.keys())
            )
        )
        params_ = {
            f"val{i}": filter_value
            for i, filter_value in enumerate(filter_by.values())
        }
        try:
            qs = session.scalars(
                select(self.model).filter(text(text_)).params(params_)
            )
        except SQLAlchemyError:
            return

        return qs.all() if to_list else qs


@dataclass
class ModelManager:
    model: Type[AbstractBaseModel]
    session: Session | scoped_session

    def count(self) -> int:
        """Calculate number of all `self.model` objects."""
        query = select(func.count(self.model.id))
        return self.session.scalar(query)
