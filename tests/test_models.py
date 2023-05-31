import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db import models

from .conf import constants
from .fixtures import create_tables, db_session, engine, user_data, users


def test_count_method_returns_number_of_all_instances(db_session, users):
    user_num = models.User.count(db_session)
    assert user_num == constants["USER_NUM"]
    assert isinstance(user_num, int)


def test_all_method_without_args_returns_scalar_result(db_session, users):
    from sqlalchemy.engine.result import ScalarResult

    user_instances = models.User.queries.all(db_session)
    assert isinstance(user_instances, ScalarResult)


def test_count_method_with_tolist_arg_returns_list_of_all_intsances(
    db_session, users
):
    user_instances = models.User.queries.all(db_session, to_list=True)
    assert isinstance(user_instances, list)
    assert len(user_instances) == constants["USER_NUM"]


def test_create_user_with_valid_data_success(db_session):
    inital_user_num = models.User.count(db_session)

    db_session.add(models.User(**user_data["test_user"]))
    db_session.commit()

    user = db_session.get(models.User, user_data["test_user"]["id"])
    assert user.tg_id == user_data["test_user"]["tg_id"]
    assert user.tg_username == user_data["test_user"]["tg_username"]

    current_user_num = models.User.count(db_session)
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


def test_create_budget_without_currency_arg_sets_default(db_session, users):
    db_session.add(models.Budget(name="test", user_id=1))
    db_session.commit()

    budget = db_session.get(models.Budget, 1)
    default_currency = models.Currency.RUB
    assert budget.currency == default_currency
