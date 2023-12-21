import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.db.exceptions import InvalidModelArgType, ModelInstanceNotFound
from app.db.models import Category, CategoryType, User
from app.utils import epoch_start

from ..conftest import MockModel

valid_user = MockModel(tg_id=100, budget_currency="EUR")
invalid_tgid_user = MockModel(tg_id="100", budget_currency="RUB")

valid_category = MockModel(
    user_id=1,
    name="test_category",
    type=CategoryType.EXPENSES,
)
invalid_arg_name_category = MockModel(
    user_id=1,
    invalid="test_category",
    type=CategoryType.EXPENSES,
)
invalid_arg_type_category = MockModel(
    user_id=1,
    name=CategoryType.INCOME,
    type=CategoryType.EXPENSES,
)
unexisting_user_id_category = MockModel(
    user_id=999999999,
    name="test_category",
    type=CategoryType.EXPENSES,
)


def test_create_user_with_valid_args(usrrep):
    from app.db.custom_types import ModelCreateResult

    result = usrrep.create_user(**valid_user)
    assert isinstance(result, ModelCreateResult)

    user, error = result.astuple()
    assert error is None
    assert isinstance(user, User)
    assert user.tg_id == valid_user.tg_id
    assert user.budget_currency == valid_user.budget_currency
    assert user.id > 0


def test_create_user_with_invalid_tg_id_type(usrrep):
    print(usrrep.create_user(**invalid_tgid_user))
    # user, error = usrrep.create_user(**invalid_tgid_user).astuple()
    # assert user is None
    # assert isinstance(error, InvalidModelArgType)
    # assert error.arg_name == "tg_id"
    # assert error.expected_type == int
    # assert error.invalid_type == str


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_get_user_with_positional_arg_raises_error(usrrep, create_users):
    usrrep.get_user(1)


def test_get_user_with_valid_kwargs(usrrep, create_users):
    valid_id, valid_tg_id = 1, 1001
    user = usrrep.get_user(user_id=valid_id)
    assert isinstance(user, User)
    assert user.id == valid_id
    assert user.tg_id == valid_tg_id

    user = usrrep.get_user(tg_id=valid_tg_id)
    assert isinstance(user, User)
    assert user.id == valid_id
    assert user.tg_id == valid_tg_id


def test_get_user_with_unexisting_ids(usrrep, create_users):
    invalid_id, invalid_tg_id = 99999, 109999
    assert usrrep.get_user(user_id=invalid_id) is None
    assert usrrep.get_user(tg_id=invalid_tg_id) is None


def test_update_user_with_valid_kwargs(usrrep, create_users):
    from app.db.custom_types import ModelUpdateDeleteResult

    valid_kwargs = {"budget_currency": "USD", "is_active": True}
    result = usrrep.update_user(1, **valid_kwargs)
    assert isinstance(result, ModelUpdateDeleteResult)

    updated, error = result.astuple()
    assert updated is True
    assert error is None


def test_update_user_without_is_active_kwarg(usrrep, create_users):
    valid_kwargs = {"budget_currency": "USD"}
    updated, error = usrrep.update_user(1, **valid_kwargs).astuple()
    assert updated is True
    assert error is None


def test_update_user_with_invalid_budget_currency(usrrep, create_users):
    invalid_kwargs = {"budget_currency": 24, "is_active": True}
    updated, error = usrrep.update_user(1, **invalid_kwargs).astuple()
    assert updated is None
    assert isinstance(error, InvalidModelArgType)
    assert error.arg_name == "budget_currency"
    assert error.expected_type == str
    assert error.invalid_type == int


def test_update_user_with_invalid_is_active(usrrep, create_users):
    invalid_kwargs = {"budget_currency": "EUR", "is_active": "invalid"}
    updated, error = usrrep.update_user(1, **invalid_kwargs).astuple()
    assert updated is None
    assert isinstance(error, InvalidModelArgType)
    assert error.arg_name == "is_active"
    assert error.expected_type == bool
    assert error.invalid_type == str


def test_delete_user_with_valid_id(usrrep, create_users):
    valid_id = 1
    deleted, error = usrrep.delete_user(valid_id).astuple()
    assert deleted is True
    assert error is None
    assert usrrep.get_user(user_id=valid_id) is None


def test_delete_user_with_invalid_id(usrrep, create_users):
    invalid_id = 199999
    deleted, error = usrrep.delete_user(invalid_id).astuple()
    assert deleted is False
    assert isinstance(error, ModelInstanceNotFound)


def test_delete_user_with_invalid_id_type(usrrep, create_users):
    invalid_id = [1, 2, 3]
    deleted, error = usrrep.delete_user(invalid_id).astuple()
    assert deleted is None
    assert isinstance(error, SQLAlchemyError)


def test_create_category_with_valid_args(catrep, create_users):
    from app.db.custom_types import ModelCreateResult

    result = catrep.create_category(**valid_category)
    assert isinstance(result, ModelCreateResult)

    category, error = result.astuple()
    assert error is None
    assert isinstance(category, Category)
    assert category.name == valid_category.name
    assert category.type == valid_category.type
    assert category.user_id == valid_category.user_id
    assert category.last_used == epoch_start()


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_create_category_with_invalid_arg_name(catrep, create_users):
    catrep.create_category(**invalid_arg_name_category)


def test_create_category_with_invalid_arg_type(catrep, create_users):
    category, error = catrep.create_category(
        **invalid_arg_type_category
    ).astuple()
    assert category is None
    assert isinstance(error, InvalidModelArgType)
    assert error.arg_name == "name"
    assert error.expected_type == str
    assert error.invalid_type == CategoryType


def test_create_category_with_unexisting_user_id(catrep, create_users):
    category, error = catrep.create_category(
        **unexisting_user_id_category
    ).astuple()
    assert category is None
    assert isinstance(error, SQLAlchemyError)


def test_get_category_with_valid_id(catrep, create_categories):
    category = catrep.create_category(**valid_category).result

    from_db = catrep.get_category(category.id)
    assert isinstance(from_db, Category)
    assert from_db.id == category.id
    assert from_db.name == category.name
    assert from_db.type == category.type


def test_get_category_with_unexisting_id(catrep, create_categories):
    assert catrep.get_category(9999) is None


def test_count_user_categories_with_existing_user_id(
    catrep, create_categories
):
    user_id = 1
    initial_count = catrep.count_user_categories(user_id)
    assert initial_count == 1

    catrep.create_category(user_id, "test_name", CategoryType.EXPENSES)
    current_count = catrep.count_user_categories(user_id)
    assert current_count == initial_count + 1


def test_count_user_categories_with_unexisting_user_id(
    catrep, create_categories
):
    assert catrep.count_user_categories(999999) == 0


def test_get_user_categories_with_existing_user_id(
    db_session, catrep, create_users
):
    from typing import Generator

    from app.db.custom_types import GeneratorResult

    user_id = 1
    sample_size = 20
    db_session.add_all(
        [
            Category(
                id=i,
                name=f"test_category{i}",
                type=CategoryType.EXPENSES if i % 2 else CategoryType.INCOME,
                user_id=user_id,
            )
            for i in range(1, sample_size + 1)
        ]
    )
    db_session.commit()

    categories = catrep.get_user_categories(user_id)
    assert isinstance(categories, GeneratorResult)
    assert categories.is_empty is False
    assert isinstance(categories.result, Generator)
    assert len(list(categories.result)) == 5  # default limit == 5.

    categories = catrep.get_user_categories(user_id, limit=10)
    assert len(list(categories.result)) == 10

    categories = catrep.get_user_categories(user_id, limit=30)
    assert len(list(categories.result)) == sample_size

    categories = catrep.get_user_categories(user_id, offset=10, limit=20)
    assert len(list(categories.result)) == sample_size - 10

    categories = catrep.get_user_categories(user_id, offset=20, limit=10)
    assert len(list(categories.result)) == 0


def test_get_user_categories_with_unexisting_user_id(
    catrep, create_categories
):
    categories = catrep.get_user_categories(999999)
    assert categories.is_empty is True
    assert categories.result == []


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_get_user_categories_with_positional_arg_raises_error(
    catrep, create_categories
):
    catrep.get_user_categories(1, 1, 1)
