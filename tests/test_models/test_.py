import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db import models
from tests.conf import constants

from .fixtures import (
    create_tables,
    create_users,
    db_session,
    engine,
    user_data,
    user_manager,
)


def test_user_class_has_expected_fields():
    expected_fieldnames = {
        "tg_id",
        "tg_username",
        "budgets",
        "id",
        "created_at",
        "last_updated",
    }
    actual_fieldnames = models.User.fieldnames
    assert isinstance(actual_fieldnames, list)
    assert expected_fieldnames == set(actual_fieldnames)


@pytest.mark.current
def test_create_user_with_valid_data_success(db_session, user_manager):
    inital_user_num = user_manager.count()

    db_session.add(models.User(**user_data["test_user"]))
    db_session.commit()

    user = user_manager.get(user_data["test_user"]["id"])
    assert user.tg_id == user_data["test_user"]["tg_id"]
    assert user.tg_username == user_data["test_user"]["tg_username"]

    current_user_num = user_manager.count()
    assert current_user_num == (inital_user_num + 1)


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_create_duplicate_user_raises_error(db_session):
    db_session.add_all(
        [
            models.User(**user_data["test_user"]),
            models.User(**user_data["test_user"]),
        ]
    )
    db_session.commit()


def test_create_budget_without_currency_arg_sets_default(
    db_session, create_users
):
    db_session.add(models.Budget(name="test", user_id=1))
    db_session.commit()

    budget = db_session.get(models.Budget, 1)
    default_currency = models.Currency.RUB
    assert budget.currency == default_currency
