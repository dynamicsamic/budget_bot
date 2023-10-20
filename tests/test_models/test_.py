import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db import models
from app.utils import now

from .fixtures import (
    create_budgets,
    create_categories,
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
        "budgets",
        "id",
        "created_at",
        "last_updated",
    }
    assert models.User.fieldnames == expected_fieldnames


def test_user_has_expected_str_representation(user_manager):
    user = user_manager.get(1)
    expected_str = f"User(Id={user.id}, TelegramId={user.tg_id})"

    assert str(user) == expected_str


def test_user_create_with_valid_data_success(db_session, user_manager):
    inital_user_num = user_manager.count()

    udata = user_data["test_user"]
    user_manager.create(**udata)

    from_orm = user_manager.get(udata["id"])
    assert from_orm.tg_id == udata["tg_id"]

    current_user_num = user_manager.count()
    assert current_user_num == (inital_user_num + 1)


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_user_unique_tg_id_constarint_raises_error(db_session, user_manager):
    user = user_manager.get(1)
    db_session.add(models.User(tg_id=user.tg_id))
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


def test_user_create_with_empty_budgets_list(user_manager):
    user = user_manager.get(1)
    assert user.budgets == []


def test_user_add_budget_appear_in_budgets_attr(db_session, user_manager):
    db_session.add(models.Budget(id=999, name="test01", user_id=1))
    db_session.commit()

    assert user_manager.get(1).budgets == [db_session.get(models.Budget, 999)]


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
    assert models.Budget.fieldnames == expected_fieldnames


def test_budget_has_expected_str_representation(db_session, create_users):
    expected_str = "Budget(Id=999, UserId=1, Currency=RUB, Name=test)"

    db_session.add(models.Budget(id=999, name="test", user_id=1))
    db_session.commit()

    budget = db_session.get(models.Budget, 999)
    assert str(budget) == expected_str


def test_create_budget_without_currency_arg_sets_default(
    db_session, create_users
):
    db_session.add(models.Budget(id=999, name="test", user_id=1))
    db_session.commit()

    budget = db_session.get(models.Budget, 999)
    default_currency = "RUB"
    assert budget.currency == default_currency


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_create_budget_with_too_long_currency_raises_error(
    db_session, create_users
):
    db_session.add(models.Budget(name="test", user_id=1, currency="too_long"))
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_create_budget_with_too_short_currency_raises_error(
    db_session, create_users
):
    db_session.add(models.Budget(name="test", user_id=1, currency="s"))
    db_session.commit()


def test_user_info_available_in_budget_instance(db_session, create_users):
    db_session.add(models.Budget(id=999, name="test", user_id=1))
    db_session.commit()

    budget = db_session.get(models.Budget, 999)
    assert isinstance(budget.user_id, int)
    assert isinstance(budget.user, models.User)


def test_budget_gets_deleted_when_user_deleted(
    db_session, user_manager, create_categories
):
    db_session.add(models.Budget(id=999, name="test", user_id=1))
    db_session.commit()

    user_manager.delete(1)
    assert db_session.get(models.Budget, 999) == None


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
    assert models.EntryCategory.fieldnames == expected_fieldnames


def test_category_has_expected_str_representation(db_session, create_budgets):
    expected_str = (
        "EntryCategory(Id=999, Name=test, Type=expenses, BudgetId=1)"
    )

    db_session.add(
        models.EntryCategory(
            id=999, name="test", type=models.EntryType.EXPENSES, budget_id=1
        )
    )
    db_session.commit()

    category = db_session.get(models.EntryCategory, 999)
    assert str(category) == expected_str


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_category_with_invalid_type_raises_error(db_session):
    db_session.add(
        models.EntryCategory(
            id=999, name="test", type="invalid_type", budget_id=1
        )
    )
    db_session.commit()


def test_category_sets_last_used_attr_to_default(db_session, create_budgets):
    import datetime as dt

    db_session.add(
        models.EntryCategory(
            id=999, name="test", type=models.EntryType.EXPENSES, budget_id=1
        )
    )
    db_session.commit()

    category = db_session.get(models.EntryCategory, 999)
    assert category.last_used == dt.datetime(year=1970, month=1, day=1)


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
    assert models.Entry.fieldnames == expected_fieldnames


def test_entry_has_expected_str_representation(db_session, create_categories):
    e = {
        "id": 1,
        "sum": 100000,
        "transaction_date": now(),
        "category_id": 1,
        "budget_id": 1,
        "description": "test",
    }
    expected_str = (
        f"Entry(Id={e['id']}, Sum={e['sum']/100:.2f}, "
        f"Date={e['transaction_date']:%Y-%m-%d %H:%M:%S}, "
        f"CategoryId={e['category_id']}, BudgetId={e['budget_id']}, "
        f"Description={e['description']})"
    )

    db_session.add(models.Entry(**e))
    db_session.commit()

    entry = db_session.get(models.Entry, e["id"])
    assert str(entry) == expected_str


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_entry_with_zero_sum_raises_error(db_session, create_categories):
    e = {
        "id": 1,
        "sum": 0,
        "transaction_date": now(),
        "category_id": 1,
        "budget_id": 1,
        "description": "test",
    }
    db_session.add(models.Entry(**e))
    db_session.commit()


def test_entry_without_description_sets_it_to_none(
    db_session, create_categories
):
    e = {
        "id": 1,
        "sum": 100000,
        "transaction_date": now(),
        "category_id": 1,
        "budget_id": 1,
    }
    db_session.add(models.Entry(**e))
    db_session.commit()

    entry = db_session.get(models.Entry, e["id"])
    assert entry.description == None
