from dataclasses import dataclass
from types import MethodType
from typing import Any, Sequence, Type

from sqlalchemy.orm import Query, Session, joinedload, scoped_session

from app.db.models import Budget, Entry, EntryCategory, User
from app.db.models.base import AbstractBaseModel

from .core import (
    DEFAULT_CASHFLOWFIELD,
    DEFAULT_DATEFIELD,
    DEFAULT_FILTERS,
    DEFAULT_ORDER_BY,
    BaseModelManager,
    CashFlowQueryManager,
    DateRangeQueryManager,
)


class ManagerSetFactory:
    def __init__(
        self,
        model: Type[AbstractBaseModel],
        managers: Sequence[Type[BaseModelManager]],
        **manager_init_kwargs: dict[str, Any],
    ) -> None:
        self.model = model
        self.managers = managers
        self.manager_init_kwargs = manager_init_kwargs

        self.manager_set = ModelManagerSet(model, **self.manager_init_kwargs)

        for manager in self.managers:
            setattr(
                self.manager_set,
                manager.__short_name__,
                ModelManagerSetMethod(manager, self.manager_set),
            )

    def get_managers(self) -> "ModelManagerSet":
        return self.manager_set


class ModelManagerSet:
    def __init__(
        self,
        model: Type[AbstractBaseModel],
        **manager_init_kwargs: dict[str, Any],
    ) -> None:
        self.model = model
        self.manager_init_kwargs = manager_init_kwargs

    def __repr__(self) -> str:
        manager_methods = [
            name
            for name, attr in self.__dict__.items()
            if callable(attr) and not name.startswith("_") and name != "model"
        ]
        return (
            f"{self.__class__.__name__}(model={self.model.__tablename__}, "
            f"managers=[{', '.join(manager_methods)}])"
        )


@dataclass
class ModelManagerSetMethod:
    manager: Type[BaseModelManager]
    manager_set: ModelManagerSet

    def __call__(self, **manager_init_kwargs: dict[str, Any]):
        return self.manager(
            self.manager_set.model, **self.filter_kwargs(manager_init_kwargs)
        )

    def filter_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        manager_set_kwargs = self.manager_set.manager_init_kwargs or {}
        for attr, value in kwargs.items():
            if attr in self.manager_fields and value is not None:
                manager_set_kwargs.update({attr: value})
        return manager_set_kwargs

    @property
    def manager_fields(self) -> set[str]:
        valid_fields = set(self.manager.__match_args__)
        valid_fields.discard("model")
        return valid_fields


UserManagers = ManagerSetFactory(
    User, [BaseModelManager, DateRangeQueryManager]
).get_managers()

BudgetManagers = ManagerSetFactory(
    Budget, [BaseModelManager, DateRangeQueryManager]
).get_managers()

CategoryManagers = ManagerSetFactory(
    EntryCategory,
    [BaseModelManager, DateRangeQueryManager],
    order_by=["-last_used", "id"],
).get_managers()


def fetch_joined(
    self, filters: Sequence[str] = None, reverse: bool = False
) -> Query[AbstractBaseModel]:
    """Fetch budget and category data when querying entries."""
    q = super(self.__class__, self)._fetch(filters, reverse)
    return q.options(
        joinedload(self.model.budget, innerjoin=True),
        joinedload(self.model.category, innerjoin=True),
    )


def EntryManager(
    manager: Type[BaseModelManager],
    session: Session | scoped_session = None,
    order_by: Sequence[str] = DEFAULT_ORDER_BY,
    filters: Sequence[str] = DEFAULT_FILTERS,
    datefield: str = DEFAULT_DATEFIELD,
    cashflowfield: str = DEFAULT_CASHFLOWFIELD,
) -> BaseModelManager:
    if manager is BaseModelManager:
        manager = manager(Entry, session, order_by, filters)
    elif manager is DateRangeQueryManager:
        manager = manager(Entry, session, order_by, filters, datefield)
    elif manager is CashFlowQueryManager:
        manager = manager(
            Entry, session, order_by, filters, datefield, cashflowfield
        )
    else:
        return

    manager._fetch = MethodType(fetch_joined, manager)
    return manager
