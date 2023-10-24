from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Budget, Entry, EntryCategory, User
from app.utils import now

from .fixtures import (
    create_budgets,
    create_categories,
    create_entries,
    create_tables,
    create_users,
    db_session,
    engine,
)


class MockModel:
    def __init__(self, **kwargs) -> None:
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __call__(self) -> dict[str, Any]:
        return self.__dict__


valid_user = MockModel(id=999, tg_id=10999)
valid_budget = MockModel(id=999, name="test_name", currency="USD", user_id=1)
valid_entry = MockModel(
    id=999,
    sum=9993991,
    transaction_date=now(),
    description="test",
    budget_id=1,
    category_id=3,
)
entry_zero_sum = MockModel(
    id=999,
    sum=0,
    transaction_date=now(),
    category_id=1,
    budget_id=1,
    description="test",
)
entry_without_budget_id = MockModel(
    id=999,
    sum=10000000,
    transaction_date=now(),
    category_id=1,
    description="test",
)
entry_without_category_id = MockModel(
    id=999,
    sum=0,
    transaction_date=now(),
    budget_id=1,
    description="test",
)
entry_without_description = MockModel(
    id=999,
    sum=9993991,
    transaction_date=now(),
    budget_id=1,
    category_id=3,
)


def test_user_class_has_expected_fields():
    expected_fieldnames = {
        "tg_id",
        "budgets",
        "id",
        "created_at",
        "last_updated",
    }
    assert User.fieldnames == expected_fieldnames


def test_user_has_expected_str_representation(db_session, create_users):
    user = db_session.get(User, 1)
    expected_str = f"User(Id={user.id}, TelegramId={user.tg_id})"

    assert str(user) == expected_str
    assert repr(user) == expected_str


def test_user_create_with_valid_data_success(db_session, create_users):
    inital_user_num = db_session.query(User).count()

    db_session.add(User(**valid_user()))
    db_session.commit()

    from_db = db_session.get(User, valid_user.id)
    assert from_db.tg_id == valid_user.tg_id

    current_user_num = db_session.query(User).count()
    assert current_user_num == inital_user_num + 1


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_user_unique_tg_id_constarint_raises_error(db_session, create_users):
    user = db_session.get(User, 1)
    db_session.add(User(tg_id=user.tg_id))
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_user_create_duplicate_raises_error(db_session, create_users):
    db_session.add_all(
        [
            User(**valid_user()),
            User(**valid_user()),
        ]
    )
    db_session.commit()


def test_user_create_with_empty_budgets_list(db_session, create_users):
    user = db_session.get(User, 1)
    assert user.budgets == []


def test_user_add_budget_appear_in_budgets_attr(db_session, create_users):
    db_session.add(Budget(id=999, name="test01", user_id=1))
    db_session.commit()

    assert db_session.get(User, 1).budgets == [db_session.get(Budget, 999)]


def test_budget_class_has_expected_fields():
    expected_fieldnames = {
        "name",
        "currency",
        "user",
        "user_id",
        "categories",
        "entries",
        "id",
        "created_at",
        "last_updated",
    }
    assert Budget.fieldnames == expected_fieldnames


def test_budget_has_expected_str_representation(db_session, create_budgets):
    budget = db_session.get(Budget, 1)
    expected_str = (
        f"Budget(Id={budget.id}, UserId={budget.user_id}, "
        f"Currency={budget.currency}, Name={budget.name})"
    )

    assert str(budget) == expected_str
    assert repr(budget) == expected_str


def test_budget_create_with_valid_data_success(db_session, create_budgets):
    inital_user_num = db_session.query(Budget).count()

    db_session.add(Budget(**valid_budget()))
    db_session.commit()

    from_db = db_session.get(Budget, valid_budget.id)
    assert from_db.name == valid_budget.name
    assert from_db.currency == valid_budget.currency
    assert from_db.user_id == valid_budget.user_id

    current_user_num = db_session.query(Budget).count()
    assert current_user_num == inital_user_num + 1


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_budget_unique_name_constarint_raises_error(
    db_session, create_budgets
):
    budget = db_session.get(Budget, 1)
    db_session.add(Budget(name=budget.name, user_id=3))
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_budget_create_duplicate_raises_error(db_session, create_budgets):
    db_session.add_all(
        [
            Budget(**valid_budget()),
            Budget(**valid_budget()),
        ]
    )
    db_session.commit()


def test_budget_create_with_empty_categories_list(db_session, create_budgets):
    budget = db_session.get(Budget, 1)
    assert budget.categories == []


def test_budget_create_with_empty_entries_list(db_session, create_budgets):
    budget = db_session.get(Budget, 1)
    assert budget.entries == []


def test_create_budget_without_currency_arg_sets_default(
    db_session, create_budgets
):
    default_currency = Budget.currency.default.arg
    budget = db_session.get(Budget, 1)
    assert budget.currency == default_currency


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_create_budget_with_too_long_currency_raises_error(
    db_session, create_users
):
    db_session.add(Budget(name="test", user_id=1, currency="too_long"))
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_create_budget_with_too_short_currency_raises_error(
    db_session, create_users
):
    db_session.add(Budget(name="test", user_id=1, currency="s"))
    db_session.commit()


def test_budget_gets_deleted_when_user_deleted(db_session, create_budgets):
    user_id = 1
    num_budgets_intial = (
        db_session.query(Budget).filter_by(user_id=user_id).count()
    )
    assert num_budgets_intial > 0

    db_session.query(User).filter_by(id=user_id).delete()
    db_session.commit()
    num_budgets_current = (
        db_session.query(Budget).filter_by(user_id=user_id).count()
    )
    assert num_budgets_current == 0


def test_category_model_has_expected_fields():
    expected_fieldnames = {
        "name",
        "type",
        "last_used",
        "budget_id",
        "budget",
        "entries",
        "id",
        "created_at",
        "last_updated",
    }
    assert EntryCategory.fieldnames == expected_fieldnames


def test_category_has_expected_str_representation(
    db_session, create_categories
):
    category = db_session.get(EntryCategory, 1)
    expected_str = (
        f"EntryCategory(Id={category.id}, Name={category.name}, "
        f"Type={category.type.value}, BudgetId={category.budget_id})"
    )

    from_db = db_session.get(EntryCategory, 1)
    assert str(from_db) == expected_str
    assert repr(from_db) == expected_str


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_category_with_invalid_type_raises_error(db_session):
    db_session.add(
        EntryCategory(id=999, name="test", type="invalid_type", budget_id=1)
    )
    db_session.commit()


def test_category_sets_last_used_attr_to_default(
    db_session, create_categories
):
    import datetime as dt

    category = db_session.get(EntryCategory, 1)
    assert category.last_used == dt.datetime(year=1970, month=1, day=1)


def test_category_gets_deleted_when_budget_deleted(
    db_session, create_categories
):
    budget_id = 1
    num_categories_intial = (
        db_session.query(EntryCategory).filter_by(budget_id=budget_id).count()
    )
    assert num_categories_intial > 0

    db_session.query(Budget).filter_by(id=budget_id).delete()
    db_session.commit()
    num_categories_current = (
        db_session.query(EntryCategory).filter_by(budget_id=budget_id).count()
    )
    assert num_categories_current == 0


def test_entry_model_has_expected_fields():
    expected_fieldnames = {
        "budget_id",
        "budget",
        "category_id",
        "category",
        "sum",
        "description",
        "transaction_date",
        "id",
        "created_at",
        "last_updated",
    }
    assert Entry.fieldnames == expected_fieldnames


def test_entry_has_expected_str_representation(db_session, create_entries):
    entry = db_session.get(Entry, 1)
    expected_str = (
        f"Entry(Id={entry.id}, Sum={entry._sum}, "
        f"Date={entry._transaction_date}, "
        f"CategoryId={entry.category_id}, BudgetId={entry.budget_id}, "
        f"Description={entry.description})"
    )

    assert str(entry) == expected_str
    assert repr(entry) == expected_str


def test_entry_create_with_valid_data_success(db_session, create_categories):
    inital_entry_num = db_session.query(Entry).count()

    db_session.add(Entry(**valid_entry()))
    db_session.commit()

    from_db = db_session.get(Entry, valid_entry.id)
    assert from_db.sum == valid_entry.sum
    assert from_db.description == valid_entry.description
    assert (
        from_db._transaction_date
        == f"{valid_entry.transaction_date:%Y-%m-%d %H:%M:%S}"
    )
    assert from_db.budget_id == valid_entry.budget_id
    assert from_db.category_id == valid_entry.category_id

    current_entry_num = db_session.query(Entry).count()
    assert current_entry_num == inital_entry_num + 1


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_entry_with_zero_sum_raises_error(db_session, create_entries):
    db_session.add(Entry(**entry_zero_sum()))
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_entry_without_budget_id_raises_error(db_session, create_entries):
    db_session.add(Entry(**entry_without_budget_id()))
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_entry_without_category_id_raises_error(db_session, create_entries):
    db_session.add(Entry(**entry_without_category_id()))
    db_session.commit()


def test_entry_without_description_sets_it_to_none(
    db_session, create_categories
):
    db_session.add(Entry(**entry_without_description()))
    db_session.commit()

    entry = db_session.get(Entry, entry_without_description.id)
    assert entry.description == None


def test_entry_gets_deleted_when_budget_deleted(db_session, create_entries):
    budget_id = 1
    num_entries_intial = (
        db_session.query(Entry).filter_by(budget_id=budget_id).count()
    )
    assert num_entries_intial > 0

    db_session.query(Budget).filter_by(id=budget_id).delete()
    db_session.commit()

    num_categories_current = (
        db_session.query(Entry).filter_by(budget_id=budget_id).count()
    )
    assert num_categories_current == 0


def test_entry_gets_deleted_when_category_deleted(db_session, create_entries):
    category_id = 1
    num_entries_intial = (
        db_session.query(Entry).filter_by(category_id=category_id).count()
    )
    assert num_entries_intial > 0

    db_session.query(Budget).filter_by(id=category_id).delete()
    db_session.commit()

    num_categories_current = (
        db_session.query(Entry).filter_by(category_id=category_id).count()
    )
    assert num_categories_current == 0
