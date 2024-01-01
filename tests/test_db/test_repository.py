import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.db.custom_types import ModelCreateResult, ModelUpdateDeleteResult
from app.db.exceptions import (
    EmptyModelKwargs,
    InvalidModelArgType,
    ModelInstanceNotFound,
)
from app.db.models import Category, CategoryType, Entry, User
from app.utils import epoch_start, now, pretty_datetime

from .conftest import (
    EXPENSES_SAMPLE,
    INCOME_SAMPLE,
    NEGATIVE_ENTRIES_SAMPLE,
    POSITIVE_ENTRIES_SAMPLE,
    TARGET_CATEGORY_ID,
    TARGET_USER_ID,
    MockModel,
)

UNEXISTING_ID = -999
TOTAL_USER_CATEGORIES = INCOME_SAMPLE + EXPENSES_SAMPLE
TARGET_USER_ENTRIES = POSITIVE_ENTRIES_SAMPLE + NEGATIVE_ENTRIES_SAMPLE
TARGET_CATEGORY_ENTRIES = TARGET_USER_ENTRIES

valid_user = MockModel(tg_id=100, budget_currency="EUR")
invalid_tgid_type_user = MockModel(tg_id="100", budget_currency="RUB")

valid_category = MockModel(
    user_id=TARGET_USER_ID,
    name="test_category",
    type=CategoryType.EXPENSES,
)
invalid_arg_name_category = MockModel(
    user_id=TARGET_USER_ID,
    invalid="test_category",
    type=CategoryType.EXPENSES,
)
invalid_arg_type_category = MockModel(
    user_id=TARGET_USER_ID,
    name=CategoryType.INCOME,
    type=CategoryType.EXPENSES,
)
unexisting_user_id_category = MockModel(
    user_id=UNEXISTING_ID,
    name="test_category",
    type=CategoryType.EXPENSES,
)

minimal_valid_entry = MockModel(
    user_id=TARGET_USER_ID, category_id=TARGET_CATEGORY_ID, sum=1000
)
full_valid_entry = MockModel(
    user_id=TARGET_USER_ID,
    category_id=TARGET_CATEGORY_ID,
    sum=-1000,
    description="test description",
    transaction_date=now(),
)
unexisting_user_id_entry = MockModel(
    user_id=UNEXISTING_ID, category_id=TARGET_CATEGORY_ID, sum=1000
)
unexisting_category_id_entry = MockModel(
    user_id=TARGET_USER_ID, category_id=UNEXISTING_ID, sum=1000
)
invalid_sum_type_entry = MockModel(
    user_id=TARGET_USER_ID, category_id=TARGET_CATEGORY_ID, sum="1000"
)
invalid_user_id_type_entry = MockModel(
    user_id="1", category_id=TARGET_CATEGORY_ID, sum=1000
)
invalid_category_id_type_entry = MockModel(
    user_id=TARGET_USER_ID, category_id="1", sum=1000
)
invalid_description_type_entry = MockModel(
    user_id=TARGET_USER_ID,
    category_id=TARGET_CATEGORY_ID,
    sum=1000,
    description=22,
)


def test_create_user_with_valid_args(usrrep):
    result = usrrep.create_user(**valid_user)
    assert isinstance(result, ModelCreateResult)

    user, error = result.astuple()
    assert error is None
    assert isinstance(user, User)
    assert user.tg_id == valid_user.tg_id
    assert user.budget_currency == valid_user.budget_currency
    assert user.id > 0


def test_create_user_with_invalid_tg_id_type(usrrep):
    user, error = usrrep.create_user(**invalid_tgid_type_user).astuple()
    assert user is None
    assert isinstance(error, InvalidModelArgType)
    assert error.arg_name == "tg_id"
    assert error.expected_type == int
    assert error.invalid_type == str


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_get_user_with_positional_arg_raises_error(usrrep, create_users):
    usrrep.get_user(1)


def test_get_user_with_valid_kwargs(usrrep, create_users):
    valid_id, valid_tg_id = 1, 101
    user = usrrep.get_user(user_id=valid_id)
    assert isinstance(user, User)
    assert user.id == valid_id
    assert user.tg_id == valid_tg_id

    user = usrrep.get_user(tg_id=valid_tg_id)
    assert isinstance(user, User)
    assert user.id == valid_id
    assert user.tg_id == valid_tg_id


def test_get_user_with_unexisting_ids(usrrep, create_users):
    invalid_id, invalid_tg_id = UNEXISTING_ID, UNEXISTING_ID
    assert usrrep.get_user(user_id=invalid_id) is None
    assert usrrep.get_user(tg_id=invalid_tg_id) is None


def test_update_user_with_valid_kwargs(usrrep, create_users):
    valid_kwargs = {"budget_currency": "USD", "is_active": True}
    result = usrrep.update_user(TARGET_USER_ID, **valid_kwargs)
    assert isinstance(result, ModelUpdateDeleteResult)

    updated, error = result.astuple()
    assert updated is True
    assert error is None


def test_update_user_without_is_active_kwarg(usrrep, create_users):
    valid_kwargs = {"budget_currency": "USD"}
    updated, error = usrrep.update_user(
        TARGET_USER_ID, **valid_kwargs
    ).astuple()
    assert updated is True
    assert error is None


def test_update_user_with_invalid_budget_currency(usrrep, create_users):
    invalid_kwargs = {"budget_currency": 24, "is_active": True}
    updated, error = usrrep.update_user(
        TARGET_USER_ID, **invalid_kwargs
    ).astuple()
    assert updated is None
    assert isinstance(error, InvalidModelArgType)
    assert error.arg_name == "budget_currency"
    assert error.expected_type == str
    assert error.invalid_type == int


def test_update_user_with_invalid_is_active(usrrep, create_users):
    invalid_kwargs = {"budget_currency": "EUR", "is_active": "invalid"}
    updated, error = usrrep.update_user(
        TARGET_USER_ID, **invalid_kwargs
    ).astuple()
    assert updated is None
    assert isinstance(error, InvalidModelArgType)
    assert error.arg_name == "is_active"
    assert error.expected_type == bool
    assert error.invalid_type == str


def test_update_user_with_empty_kwargs(usrrep, create_users):
    result, error = usrrep.update_user(TARGET_USER_ID).astuple()
    assert result is None
    assert isinstance(error, EmptyModelKwargs)


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_user_with_positional_args(usrrep, create_users):
    usrrep.update_user(TARGET_USER_ID, "currency", False)


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_user_with_invalid_arg_name(usrrep, create_users):
    usrrep.update_user(TARGET_USER_ID, invalid=True)


def test_delete_user_with_valid_id(usrrep, create_users):
    deleted, error = usrrep.delete_user(TARGET_USER_ID).astuple()
    assert deleted is True
    assert error is None
    assert usrrep.get_user(user_id=TARGET_USER_ID) is None


def test_delete_user_with_invalid_id(usrrep, create_users):
    deleted, error = usrrep.delete_user(UNEXISTING_ID).astuple()
    assert deleted is False
    assert isinstance(error, ModelInstanceNotFound)


def test_delete_user_with_invalid_id_type(usrrep, create_users):
    invalid_id = [1, 2, 3]
    deleted, error = usrrep.delete_user(invalid_id).astuple()
    assert deleted is None
    assert isinstance(error, SQLAlchemyError)


def test_create_category_with_valid_args(catrep, create_users):
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
    assert catrep.get_category(UNEXISTING_ID) is None


def test_count_user_categories_with_existing_user_id(
    catrep, create_categories
):
    initial_count = catrep.count_user_categories(TARGET_USER_ID)
    assert initial_count == TOTAL_USER_CATEGORIES

    catrep.create_category(TARGET_USER_ID, "test_name", CategoryType.EXPENSES)
    current_count = catrep.count_user_categories(TARGET_USER_ID)
    assert current_count == initial_count + 1


def test_count_user_categories_with_unexisting_user_id(
    catrep, create_categories
):
    assert catrep.count_user_categories(UNEXISTING_ID) == 0


def test_update_category_with_valid_kwargs(catrep, create_categories):
    original_category = catrep.get_category(TARGET_CATEGORY_ID)
    original_type = original_category.type
    original_id = original_category.id
    original_created_at = original_category.created_at
    original_last_updated = original_category.last_updated

    valid_kwargs = {
        "name": "valid",
        "last_used": now(),
        "num_entries": 10,
    }

    result = catrep.update_category(TARGET_CATEGORY_ID, **valid_kwargs)
    assert isinstance(result, ModelUpdateDeleteResult)

    updated, error = result.astuple()
    assert error is None
    assert updated is True

    updated_category = catrep.get_category(TARGET_CATEGORY_ID)
    assert updated_category.name == valid_kwargs["name"]
    assert updated_category.num_entries == valid_kwargs["num_entries"]
    assert pretty_datetime(updated_category.last_used) == pretty_datetime(
        valid_kwargs["last_used"]
    )

    assert updated_category.type == original_type
    assert updated_category.id == original_id
    assert updated_category.created_at == original_created_at
    assert updated_category.last_updated != original_last_updated


def test_update_category_with_invalid_type_kwargs(catrep, create_categories):
    invalid_kwargs = {
        "name": ["invalid"],
        "last_used": now(),
        "num_entries": "10",
    }

    result, error = catrep.update_category(
        TARGET_CATEGORY_ID, **invalid_kwargs
    ).astuple()

    assert result is None
    assert isinstance(error, InvalidModelArgType)
    assert error.model == Category
    assert error.arg_name == "name"
    assert error.expected_type == str
    assert error.invalid_type == list


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_category_with_invalid_arg_name(catrep, create_categories):
    catrep.update_category(TARGET_CATEGORY_ID, invalid="name")


def test_update_category_without_kwargs(catrep, create_categories):
    updated, error = catrep.update_category(TARGET_CATEGORY_ID).astuple()
    assert updated is None
    assert isinstance(error, EmptyModelKwargs)


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_category_with_positional_args(catrep, create_categories):
    catrep.update_category(
        TARGET_CATEGORY_ID, "new_name", CategoryType.EXPENSES
    )


def test_delete_category_with_valid_id(catrep, create_categories):
    result = catrep.delete_category(TARGET_CATEGORY_ID)
    assert isinstance(result, ModelUpdateDeleteResult)

    deleted, error = result.astuple()
    assert deleted is True
    assert error is None


def test_delete_category_with_unexisting_id(catrep, create_categories):
    deleted, error = catrep.delete_category(UNEXISTING_ID).astuple()
    assert deleted is False
    assert isinstance(error, ModelInstanceNotFound)


def test_delete_category_with_invalid_id_type(catrep, create_categories):
    deleted, error = catrep.delete_category([TARGET_CATEGORY_ID]).astuple()
    assert deleted is None
    assert isinstance(error, SQLAlchemyError)


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
    categories = catrep.get_user_categories(UNEXISTING_ID)
    assert categories.is_empty is True
    assert categories.result == []


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_get_user_categories_with_positional_arg_raises_error(
    catrep, create_categories
):
    catrep.get_user_categories(1, 1, 1)


def test_category_exists_with_valid_category_id(catrep, create_categories):
    assert catrep.category_exists(category_id=TARGET_CATEGORY_ID) is True
    assert (
        catrep.category_exists(
            category_id=TARGET_CATEGORY_ID, user_id=UNEXISTING_ID
        )
        is True
    )


def test_category_exists_with_unexisting_category_id(
    catrep, create_categories
):
    assert catrep.category_exists(category_id=UNEXISTING_ID) is False


def test_category_exists_with_valid_user_id(catrep, create_categories):
    assert catrep.category_exists(user_id=TARGET_USER_ID) is True
    assert (
        catrep.category_exists(
            category_id=UNEXISTING_ID, user_id=TARGET_USER_ID
        )
        is True
    )


def test_category_exists_with_unexisting_user_id(catrep, create_categories):
    assert catrep.category_exists(user_id=UNEXISTING_ID) is False


def test_category_exists_with_valid_category_name_arg(
    catrep, create_categories
):
    catrep.create_category(**valid_category)

    assert (
        catrep.category_exists(
            user_id=valid_category.user_id, category_name=valid_category.name
        )
        is True
    )


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_category_exists_with_positional_arg_raises_error(
    catrep, create_categories
):
    catrep.category_exists(1, 1)


def test_create_entry_with_minimal_valid_args(entrep, create_categories):
    result = entrep.create_entry(**minimal_valid_entry)
    assert isinstance(result, ModelCreateResult)

    entry, error = result.astuple()
    assert error is None

    assert isinstance(entry, Entry)
    assert entry.user_id == minimal_valid_entry.user_id
    assert entry.category_id == minimal_valid_entry.category_id
    assert entry.sum == minimal_valid_entry.sum
    assert entry.id > 0
    assert entry.description is None
    assert entry.transaction_date is not None


def test_create_entry_with_full_valid_args(entrep, create_categories):
    entry, error = entrep.create_entry(**full_valid_entry).astuple()
    assert error is None
    assert entry.user_id == full_valid_entry.user_id
    assert entry.category_id == full_valid_entry.category_id
    assert entry.sum == full_valid_entry.sum
    assert entry.id > 0
    assert entry.description == full_valid_entry.description

    assert pretty_datetime(entry.transaction_date) == pretty_datetime(
        full_valid_entry.transaction_date
    )


def test_create_entry_with_unexisting_user_id(entrep, create_categories):
    result = entrep.create_entry(**unexisting_user_id_entry)
    assert isinstance(result, ModelCreateResult)

    entry, error = result.astuple()
    assert entry is None
    assert isinstance(error, SQLAlchemyError)


def test_create_entry_with_unexisting_category_id(entrep, create_categories):
    result = entrep.create_entry(**unexisting_category_id_entry)
    assert isinstance(result, ModelCreateResult)

    entry, error = result.astuple()
    assert entry is None
    assert isinstance(error, SQLAlchemyError)


def test_create_entry_with_invalid_arg_types(entrep, create_categories):
    category, error = entrep.create_entry(
        **invalid_user_id_type_entry
    ).astuple()
    assert category is None
    assert isinstance(error, InvalidModelArgType)
    assert error.arg_name == "user_id"
    assert error.expected_type == int
    assert error.invalid_type == str

    category, error = entrep.create_entry(
        **invalid_category_id_type_entry
    ).astuple()
    assert category is None
    assert isinstance(error, InvalidModelArgType)
    assert error.arg_name == "category_id"
    assert error.expected_type == int
    assert error.invalid_type == str

    category, error = entrep.create_entry(
        **invalid_description_type_entry
    ).astuple()
    assert category is None
    assert isinstance(error, InvalidModelArgType)
    assert error.arg_name == "description"
    assert error.expected_type == str
    assert error.invalid_type == int


def test_get_entry_with_valid_id(entrep, create_entries):
    entry = entrep.create_entry(**minimal_valid_entry).result

    from_db = entrep.get_entry(entry.id)
    assert isinstance(from_db, Entry)
    assert from_db.id == entry.id
    assert from_db.user_id == entry.user_id
    assert from_db.category_id == entry.category_id
    assert from_db.sum == entry.sum


def test_get_entry_with_unexisting_id(entrep, create_entries):
    assert entrep.get_entry(UNEXISTING_ID) is None


def test_count_entries_with_valid_user_id(entrep, create_entries):
    initial_count = entrep.count_entries(user_id=TARGET_USER_ID)
    assert initial_count == TARGET_USER_ENTRIES

    entrep.create_entry(**minimal_valid_entry)
    assert entrep.count_entries(user_id=TARGET_USER_ID) == initial_count + 1

    assert entrep.count_entries(user_id=TARGET_USER_ID + 1) == 0


def test_count_entries_with_valid_category_id(entrep, create_entries):
    initial_count = entrep.count_entries(category_id=TARGET_CATEGORY_ID)
    assert initial_count == TARGET_CATEGORY_ENTRIES

    entrep.create_entry(**minimal_valid_entry)
    assert (
        entrep.count_entries(category_id=TARGET_CATEGORY_ID)
        == initial_count + 1
    )

    assert entrep.count_entries(category_id=TARGET_CATEGORY_ID + 1) == 0


def test_count_entries_with_combined_valid_and_invalid_ids(
    entrep, create_entries
):
    assert (
        entrep.count_entries(user_id=TARGET_USER_ID, category_id=UNEXISTING_ID)
        == TARGET_USER_ENTRIES
    )

    assert (
        entrep.count_entries(
            user_id=UNEXISTING_ID, category_id=TARGET_CATEGORY_ID
        )
        == TARGET_CATEGORY_ENTRIES
    )


def test_count_entries_with_unexisting_ids(entrep, create_entries):
    assert (
        entrep.count_entries(user_id=UNEXISTING_ID, category_id=UNEXISTING_ID)
        == 0
    )


def test_count_entries_without_args(entrep, create_entries):
    assert entrep.count_entries() == 0


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_count_entries_with_positional_args(entrep, create_entries):
    entrep.count_entries(TARGET_USER_ID, TARGET_CATEGORY_ID)
