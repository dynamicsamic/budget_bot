import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db import models
from app.utils import now
from tests.conf import constants

from .fixtures import (
    create_budgets,
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
    assert models.User.fieldnames == expected_fieldnames


def test_user_has_expected_str_representation(user_manager):
    user = user_manager.get(1)
    expected_str = (
        f"{user.__class__.__name__}(Id={user.id} "
        f"TelegramName={user.tg_username}, TelegramId={user.tg_id})"
    )

    assert str(user) == expected_str


def test_user_create_with_valid_data_success(db_session, user_manager):
    inital_user_num = user_manager.count()

    db_session.add(models.User(**user_data["test_user"]))
    db_session.commit()

    user = user_manager.get(user_data["test_user"]["id"])
    assert user.tg_id == user_data["test_user"]["tg_id"]
    assert user.tg_username == user_data["test_user"]["tg_username"]

    current_user_num = user_manager.count()
    assert current_user_num == (inital_user_num + 1)


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_user_unique_tg_id_constarint_raises_error(db_session, user_manager):
    user = user_manager.get(1)
    payload = {"tg_id": user.tg_id, "tg_username": "new_user_name"}
    db_session.add(models.User(**payload))
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_user_unique_tg_username_constarint_raises_error(
    db_session, user_manager
):
    user = user_manager.get(1)
    payload = {"tg_id": 100001001, "tg_username": user.tg_username}
    db_session.add(models.User(**payload))
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_user_create_duplicate_raises_error(db_session):
    db_session.add_all(
        [
            models.User(**user_data["test_user"]),
            models.User(**user_data["test_user"]),
        ]
    )
    db_session.commit()


def test_budget_class_has_expected_fields():
    expected_fieldnames = {
        "name",
        "currency",
        "user",
        "user_id",
        "entries",
        "id",
        "created_at",
        "last_updated",
    }
    assert models.Budget.fieldnames == expected_fieldnames


def test_budget_has_expected_str_representation(db_session, create_users):
    expected_str = "Budget(Id=999, UserId=1, Cur=RUB, Name=test)"

    db_session.add(models.Budget(id=999, name="test", user_id=1))
    db_session.commit()

    budget = db_session.get(models.Budget, 999)
    assert str(budget) == expected_str


def test_create_budget_without_currency_arg_sets_default(
    db_session, create_users
):
    db_session.add(models.Budget(name="test", user_id=1))
    db_session.commit()

    budget = db_session.get(models.Budget, 1)
    default_currency = models.Currency.RUB
    assert budget.currency == default_currency
