import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from db import models

from .conf import constants
from .fixtures import db_session, test_user, user_data, users


def test_startup(db_session, users):
    pass


def test_count_method_returns_number_of_all_instances(db_session):
    user_num = models.User.count(db_session)
    assert user_num == constants["USER_NUM"]
    assert isinstance(user_num, int)


def test_count_method_without_args_returns_scalar_result(db_session):
    from sqlalchemy.engine.result import ScalarResult

    user_instances = models.User.all(db_session)
    assert isinstance(user_instances, ScalarResult)


def test_count_method_with_tolist_arg_returns_list_of_all_intsances(
    db_session,
):
    user_instances = models.User.all(db_session, to_list=True)
    assert isinstance(user_instances, list)
    assert len(user_instances) == constants["USER_NUM"]


def test_create_user_with_valid_data_success(db_session, test_user):
    inital_user_num = models.User.count(db_session)

    db_session.add(test_user)
    db_session.commit()

    user = db_session.get(models.User, user_data["test_user"]["id"])
    assert user.tg_id == user_data["test_user"]["tg_id"]
    assert user.tg_username == user_data["test_user"]["tg_username"]
    current_user_num = models.User.count(db_session)
    assert current_user_num == (inital_user_num + 1)


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_create_user_with_existing_data_raises_error(db_session):
    # need to construct new object;
    # otherwise session doesn't add test_user
    existing_user = models.User(**user_data["test_user"])
    db_session.add(existing_user)
    db_session.commit()
