import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import Category, CategoryType, Entry, User
from app.db.repository import CommonRepository
from app.exceptions import (
    EmptyModelKwargs,
    InvalidModelArgType,
    ModelInstanceNotFound,
    RepositoryValidationError,
)
from app.utils import epoch_start, now, pretty_datetime

from ..test_utils import (
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
TARGET_ENTRY_ID = TARGET_CATEGORY_ID

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


def test_create_repository(inmemory_db_session):
    assert CommonRepository(inmemory_db_session, User)


@pytest.mark.xfail(raises=RepositoryValidationError, strict=True)
def test_create_repository_invalid_session():
    CommonRepository("invalid", User)


@pytest.mark.xfail(raises=RepositoryValidationError, strict=True)
def test_create_repository_inactive_session():
    from unittest.mock import MagicMock, patch

    # need to pass isinstance() check
    with patch("app.db.repository.isinstance", return_value=True):
        session = MagicMock()
        session.is_active = False
        CommonRepository(session, User)


@pytest.mark.xfail(raises=RepositoryValidationError, strict=True)
def test_create_repository_invalid_model_type(inmemory_db_session):
    CommonRepository(inmemory_db_session, str)


@pytest.mark.xfail(raises=RepositoryValidationError, strict=True)
def test_create_repository_invalid_model_obj(inmemory_db_session):
    CommonRepository(inmemory_db_session, "invalid")


def test_create_user(usrrep):
    user = usrrep.create_user(**valid_user)
    assert isinstance(user, User)
    assert user.tg_id == valid_user.tg_id
    assert user.budget_currency == valid_user.budget_currency
    assert user.id > 0


@pytest.mark.xfail(raises=InvalidModelArgType, strict=True)
def test_create_user_invalid_type_tg_id(usrrep):
    usrrep.create_user(**invalid_tgid_type_user)


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_get_user_positional_arg(usrrep, create_inmemory_users):
    usrrep.get_user(1)


def test_get_user(usrrep, create_inmemory_users):
    valid_id, valid_tg_id = 1, 101
    user = usrrep.get_user(user_id=valid_id)
    assert isinstance(user, User)
    assert user.id == valid_id
    assert user.tg_id == valid_tg_id

    user = usrrep.get_user(tg_id=valid_tg_id)
    assert isinstance(user, User)
    assert user.id == valid_id
    assert user.tg_id == valid_tg_id


def test_get_unexisting_user(usrrep, create_inmemory_users):
    invalid_id, invalid_tg_id = UNEXISTING_ID, UNEXISTING_ID
    assert usrrep.get_user(user_id=invalid_id) is None
    assert usrrep.get_user(tg_id=invalid_tg_id) is None


def test_update_user(usrrep, create_inmemory_users):
    budget_currency, is_active = "USD", True
    updated = usrrep.update_user(
        TARGET_USER_ID, budget_currency=budget_currency, is_active=is_active
    )
    assert isinstance(updated, User)
    assert updated.budget_currency == budget_currency
    assert updated.is_active == is_active

    from_db = usrrep.get_user(user_id=TARGET_USER_ID)
    assert from_db == updated


@pytest.mark.xfail(raises=ModelInstanceNotFound, strict=True)
def test_update_unexisting_user(usrrep, create_inmemory_users):
    usrrep.update_user(UNEXISTING_ID, budget_currency="USD", is_active=True)


def test_update_user_without_is_active_kwarg(usrrep, create_inmemory_users):
    updated = usrrep.update_user(TARGET_USER_ID, budget_currency="USD")
    assert isinstance(updated, User)
    assert updated.id == TARGET_USER_ID


@pytest.mark.xfail(raises=InvalidModelArgType, strict=True)
def test_update_user_invalid_budget_currency(usrrep, create_inmemory_users):
    usrrep.update_user(TARGET_USER_ID, budget_currency=24, is_active=True)


@pytest.mark.xfail(raises=InvalidModelArgType, strict=True)
def test_update_user_invalid_is_active(usrrep, create_inmemory_users):
    usrrep.update_user(
        TARGET_USER_ID, budget_currency="EUR", is_active="invalid"
    )


@pytest.mark.xfail(raises=EmptyModelKwargs, strict=True)
def test_update_user_empty_kwargs(usrrep, create_inmemory_users):
    usrrep.update_user(TARGET_USER_ID)


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_user_positional_args(usrrep, create_inmemory_users):
    usrrep.update_user(TARGET_USER_ID, "currency", False)


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_user_invalid_arg_name(usrrep, create_inmemory_users):
    usrrep.update_user(TARGET_USER_ID, invalid=True)


def test_delete_user(usrrep, create_inmemory_users):
    assert usrrep.delete_user(TARGET_USER_ID) is True
    assert usrrep.get_user(user_id=TARGET_USER_ID) is None


@pytest.mark.xfail(raises=ModelInstanceNotFound, strict=True)
def test_delete_unexisting_user(usrrep, create_inmemory_users):
    usrrep.delete_user(UNEXISTING_ID)


@pytest.mark.xfail(raises=SQLAlchemyError, strict=True)
def test_delete_user_invalid_type_id(usrrep, create_inmemory_users):
    usrrep.delete_user([1, 2, 3])


def test_create_category(catrep, create_inmemory_users):
    category = catrep.create_category(**valid_category)
    assert isinstance(category, Category)
    assert category.name == valid_category.name
    assert category.type == valid_category.type
    assert category.user_id == valid_category.user_id
    assert category.last_used == epoch_start()


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_create_category_invalid_arg_name(catrep, create_inmemory_users):
    catrep.create_category(**invalid_arg_name_category)


@pytest.mark.xfail(raises=InvalidModelArgType, strict=True)
def test_create_category_invalid_arg_type(catrep, create_inmemory_users):
    catrep.create_category(**invalid_arg_type_category)


@pytest.mark.xfail(raises=SQLAlchemyError, strict=True)
def test_create_category_unexisting_user_id(catrep, create_inmemory_users):
    catrep.create_category(**unexisting_user_id_category)


def test_get_category(catrep, create_inmemory_categories):
    category = catrep.create_category(**valid_category)

    from_db = catrep.get_category(category.id)
    assert isinstance(from_db, Category)
    assert from_db.id == category.id
    assert from_db.name == category.name
    assert from_db.type == category.type


def test_get_unexisting_category(catrep, create_inmemory_categories):
    assert catrep.get_category(UNEXISTING_ID) is None


def test_count_user_categories(catrep, create_inmemory_categories):
    initial_count = catrep.count_user_categories(TARGET_USER_ID)
    assert initial_count == TOTAL_USER_CATEGORIES

    income_count = catrep.count_user_categories(
        TARGET_USER_ID, category_type=CategoryType.INCOME
    )
    assert income_count == INCOME_SAMPLE

    expenses_count = catrep.count_user_categories(
        TARGET_USER_ID, category_type=CategoryType.EXPENSES
    )
    assert expenses_count == EXPENSES_SAMPLE

    catrep.create_category(TARGET_USER_ID, "test_name", CategoryType.EXPENSES)
    current_count = catrep.count_user_categories(TARGET_USER_ID)
    assert current_count == initial_count + 1


def test_count_unexisting_user_categories(catrep, create_inmemory_categories):
    assert catrep.count_user_categories(UNEXISTING_ID) == 0


def test_update_category(catrep, create_inmemory_categories):
    valid_kwargs = {
        "name": "valid",
        "last_used": now(),
        "num_entries": 10,
    }

    updated = catrep.update_category(TARGET_CATEGORY_ID, **valid_kwargs)
    assert isinstance(updated, Category)
    from_db = catrep.get_category(TARGET_CATEGORY_ID)
    assert updated.name == valid_kwargs["name"]
    assert updated.num_entries == valid_kwargs["num_entries"]
    assert pretty_datetime(updated.last_used) == pretty_datetime(
        valid_kwargs["last_used"]
    )
    assert updated == from_db


@pytest.mark.xfail(raises=InvalidModelArgType, strict=True)
def test_update_category_invalid_kwargs_type(
    catrep, create_inmemory_categories
):
    catrep.update_category(
        TARGET_CATEGORY_ID,
        name=["invalid"],
        last_used=now(),
        num_entries="10",
    )


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_category_invalid_arg_name(catrep, create_inmemory_categories):
    catrep.update_category(TARGET_CATEGORY_ID, invalid="name")


@pytest.mark.xfail(raises=EmptyModelKwargs, strict=True)
def test_update_category_without_kwargs(catrep, create_inmemory_categories):
    catrep.update_category(TARGET_CATEGORY_ID)


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_category_positional_args(catrep, create_inmemory_categories):
    catrep.update_category(
        TARGET_CATEGORY_ID, "new_name", CategoryType.EXPENSES
    )


def test_delete_category(catrep, create_inmemory_categories):
    assert catrep.delete_category(TARGET_CATEGORY_ID) is True


@pytest.mark.xfail(raises=ModelInstanceNotFound, strict=True)
def test_delete_unexisting_category(catrep, create_inmemory_categories):
    catrep.delete_category(UNEXISTING_ID)


@pytest.mark.xfail(raises=SQLAlchemyError, strict=True)
def test_delete_category_invalid_type_id(catrep, create_inmemory_categories):
    catrep.delete_category([TARGET_CATEGORY_ID])


def test_get_user_categories(
    inmemory_db_session, catrep, create_inmemory_users
):
    from typing import Generator

    from app.custom_types import GeneratorResult

    user_id = 1
    sample_size = 20
    inmemory_db_session.add_all(
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
    inmemory_db_session.commit()

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


def test_user_income_and_expenses(catrep, create_inmemory_categories):
    expenses = catrep.get_user_categories(
        TARGET_USER_ID, limit=100, category_type=CategoryType.EXPENSES
    )
    assert len(list(expenses.result)) == EXPENSES_SAMPLE

    income = catrep.get_user_categories(
        TARGET_USER_ID, limit=100, category_type=CategoryType.INCOME
    )
    assert len(list(income.result)) == INCOME_SAMPLE


def test_get_unexisting_user_categories(catrep, create_inmemory_categories):
    categories = catrep.get_user_categories(UNEXISTING_ID)
    assert categories.is_empty is True
    assert categories.result == []


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_get_user_categories_positional_args(
    catrep, create_inmemory_categories
):
    catrep.get_user_categories(1, 1, 1)


def test_category_exists(catrep, create_inmemory_categories):
    assert catrep.category_exists(category_id=TARGET_CATEGORY_ID) is True
    assert (
        catrep.category_exists(
            category_id=TARGET_CATEGORY_ID, user_id=UNEXISTING_ID
        )
        is True
    )


def test_unexisting_category_exists(catrep, create_inmemory_categories):
    assert catrep.category_exists(category_id=UNEXISTING_ID) is False


def test_category_exists_existing_user(catrep, create_inmemory_categories):
    assert catrep.category_exists(user_id=TARGET_USER_ID) is True
    assert (
        catrep.category_exists(
            category_id=UNEXISTING_ID, user_id=TARGET_USER_ID
        )
        is True
    )


def test_category_exists_unexisting_user(catrep, create_inmemory_categories):
    assert catrep.category_exists(user_id=UNEXISTING_ID) is False


def test_category_exists_valid_category_name(
    catrep, create_inmemory_categories
):
    catrep.create_category(**valid_category)

    assert (
        catrep.category_exists(
            user_id=valid_category.user_id, category_name=valid_category.name
        )
        is True
    )


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_category_exists_positional_args(catrep, create_inmemory_categories):
    catrep.category_exists(1, 1)


def test_count_category_entries(
    inmemory_db_session, catrep, create_inmemory_categories
):
    initial_entry_count = catrep.count_category_entries(TARGET_CATEGORY_ID)
    assert initial_entry_count == 0

    inmemory_db_session.add_all(
        [
            Entry(
                id=i,
                sum=100,
                user_id=TARGET_USER_ID,
                category_id=TARGET_CATEGORY_ID,
            )
            for i in range(1, 11)
        ]
    )
    inmemory_db_session.commit()

    current_entry_count = catrep.count_category_entries(TARGET_CATEGORY_ID)
    assert current_entry_count == initial_entry_count + 10

    assert catrep.count_category_entries(UNEXISTING_ID) == 0


def test_create_entry_minimal_valid_args(entrep, create_inmemory_categories):
    entry = entrep.create_entry(**minimal_valid_entry)
    assert isinstance(entry, Entry)
    assert entry.user_id == minimal_valid_entry.user_id
    assert entry.category_id == minimal_valid_entry.category_id
    assert entry.sum == minimal_valid_entry.sum
    assert entry.id > 0
    assert entry.description is None
    assert entry.transaction_date is not None


def test_create_entry_full_valid_args(entrep, create_inmemory_categories):
    entry = entrep.create_entry(**full_valid_entry)
    assert entry.user_id == full_valid_entry.user_id
    assert entry.category_id == full_valid_entry.category_id
    assert entry.sum == full_valid_entry.sum
    assert entry.id > 0
    assert entry.description == full_valid_entry.description
    assert pretty_datetime(entry.transaction_date) == pretty_datetime(
        full_valid_entry.transaction_date
    )


@pytest.mark.xfail(raises=SQLAlchemyError, strict=True)
def test_create_entry_unexisting_user(entrep, create_inmemory_categories):
    entrep.create_entry(**unexisting_user_id_entry)


@pytest.mark.xfail(raises=SQLAlchemyError, strict=True)
def test_create_entry_unexisting_category(entrep, create_inmemory_categories):
    entrep.create_entry(**unexisting_category_id_entry)


@pytest.mark.xfail(raises=InvalidModelArgType, strict=True)
def test_create_entry_invalid_type_user_id(entrep, create_inmemory_categories):
    entrep.create_entry(**invalid_user_id_type_entry)


@pytest.mark.xfail(raises=InvalidModelArgType, strict=True)
def test_create_entry_invalid_type_category_id(
    entrep, create_inmemory_categories
):
    entrep.create_entry(**invalid_category_id_type_entry)


@pytest.mark.xfail(raises=InvalidModelArgType, strict=True)
def test_create_entry_invalid_type_description(
    entrep, create_inmemory_categories
):
    entrep.create_entry(**invalid_description_type_entry)


def test_get_entry(entrep, create_inmemory_entries):
    entry = entrep.create_entry(**minimal_valid_entry)

    from_db = entrep.get_entry(entry.id)
    assert isinstance(from_db, Entry)
    assert from_db.id == entry.id
    assert from_db.user_id == entry.user_id
    assert from_db.category_id == entry.category_id
    assert from_db.sum == entry.sum


def test_get_unexisting_entry(entrep, create_inmemory_entries):
    assert entrep.get_entry(UNEXISTING_ID) is None


def test_count_entries_existing_user(entrep, create_inmemory_entries):
    initial_count = entrep.count_entries(user_id=TARGET_USER_ID)
    assert initial_count == TARGET_USER_ENTRIES

    entrep.create_entry(**minimal_valid_entry)
    assert entrep.count_entries(user_id=TARGET_USER_ID) == initial_count + 1

    assert entrep.count_entries(user_id=TARGET_USER_ID + 1) == 0


def test_count_entries_existing_category(entrep, create_inmemory_entries):
    initial_count = entrep.count_entries(category_id=TARGET_CATEGORY_ID)
    assert initial_count == TARGET_CATEGORY_ENTRIES

    entrep.create_entry(**minimal_valid_entry)
    assert (
        entrep.count_entries(category_id=TARGET_CATEGORY_ID)
        == initial_count + 1
    )

    assert entrep.count_entries(category_id=TARGET_CATEGORY_ID + 1) == 0


def test_count_entries_mixed_ids(entrep, create_inmemory_entries):
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


def test_count_entries_unexisting_ids(entrep, create_inmemory_entries):
    assert (
        entrep.count_entries(user_id=UNEXISTING_ID, category_id=UNEXISTING_ID)
        == 0
    )


def test_count_entries_without_args(entrep, create_inmemory_entries):
    assert entrep.count_entries() == 0


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_count_entries_positional_args(entrep, create_inmemory_entries):
    entrep.count_entries(TARGET_USER_ID, TARGET_CATEGORY_ID)


def test_update_entry(entrep, create_inmemory_entries):
    valid_kwargs = {
        "sum": 1000,
        "transaction_date": now(),
    }

    updated = entrep.update_entry(TARGET_ENTRY_ID, **valid_kwargs)
    assert isinstance(updated, Entry)
    assert updated.sum == valid_kwargs["sum"]
    assert pretty_datetime(updated.transaction_date) == pretty_datetime(
        valid_kwargs["transaction_date"]
    )
    from_db = entrep.get_entry(TARGET_ENTRY_ID)
    assert updated == from_db


def test_update_entry_assign_to_another_category(
    entrep, create_inmemory_entries
):
    initial_entry_count = entrep.count_entries(category_id=TARGET_CATEGORY_ID)
    original_category_id = entrep.get_entry(TARGET_ENTRY_ID).category_id

    updated = entrep.update_entry(TARGET_ENTRY_ID, category_id=2)
    assert updated.category_id != original_category_id
    assert (
        entrep.count_entries(category_id=TARGET_CATEGORY_ID)
        == initial_entry_count - 1
    )


@pytest.mark.xfail(raises=InvalidModelArgType, strict=True)
def test_update_entry_invalid_type_kwargs(entrep, create_inmemory_entries):
    entrep.update_entry(
        TARGET_ENTRY_ID,
        sum="26055",
        description=26,
    )


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_entry_invalid_arg_name(entrep, create_inmemory_entries):
    entrep.update_entry(TARGET_ENTRY_ID, invalid="name")


@pytest.mark.xfail(raises=EmptyModelKwargs, strict=True)
def test_update_entry_without_kwargs(entrep, create_inmemory_entries):
    entrep.update_entry(TARGET_ENTRY_ID)


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_update_entry_positional_args(entrep, create_inmemory_entries):
    entrep.update_entry(TARGET_ENTRY_ID, 22000, "description")


@pytest.mark.xfail(raises=ModelInstanceNotFound, strict=True)
def test_update_unexisting_entry(entrep, create_inmemory_entries):
    assert entrep.update_entry(UNEXISTING_ID, sum=100)


def test_delete_entry(entrep, create_inmemory_entries):
    assert entrep.delete_entry(TARGET_ENTRY_ID) is True


@pytest.mark.xfail(raises=ModelInstanceNotFound, strict=True)
def test_delete_unexisting_entry(entrep, create_inmemory_entries):
    assert entrep.delete_entry(UNEXISTING_ID)


@pytest.mark.xfail(raises=SQLAlchemyError, strict=True)
def test_delete_entry_invalid_type_id(entrep, create_inmemory_entries):
    entrep.delete_entry([TARGET_ENTRY_ID])


def test_entry_exists(entrep, create_inmemory_entries):
    assert entrep.entry_exists(entry_id=TARGET_ENTRY_ID) is True
    assert (
        entrep.entry_exists(
            entry_id=TARGET_ENTRY_ID,
            category_id=UNEXISTING_ID,
            user_id=UNEXISTING_ID,
        )
        is True
    )


def test_unexisting_entry_exists(entrep, create_inmemory_entries):
    assert entrep.entry_exists(entry_id=UNEXISTING_ID) is False


def test_entry_exists_existing_category(entrep, create_inmemory_entries):
    assert entrep.entry_exists(category_id=TARGET_CATEGORY_ID) is True
    assert (
        entrep.entry_exists(
            category_id=TARGET_CATEGORY_ID,
            entry_id=UNEXISTING_ID,
            user_id=UNEXISTING_ID,
        )
        is True
    )


def test_entry_exists_unexisting_category(entrep, create_inmemory_entries):
    assert entrep.entry_exists(category_id=UNEXISTING_ID) is False


def test_entry_exists_existing_user(entrep, create_inmemory_entries):
    assert entrep.entry_exists(user_id=TARGET_USER_ID) is True
    assert (
        entrep.entry_exists(
            user_id=TARGET_USER_ID,
            entry_id=UNEXISTING_ID,
            category_id=UNEXISTING_ID,
        )
        is True
    )


def test_entry_exists_unexisting_user(entrep, create_inmemory_entries):
    assert entrep.entry_exists(user_id=UNEXISTING_ID) is False


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_entry_exists_positional_args(entrep, create_inmemory_entries):
    entrep.entry_exists(TARGET_ENTRY_ID, TARGET_USER_ID, TARGET_CATEGORY_ID)
