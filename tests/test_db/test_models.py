import pytest
from sqlalchemy import DateTime, Integer
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    AbstractBaseModel,
    Category,
    CategoryType,
    Entry,
    User,
)
from app.utils import now

from .conftest import MockModel

#########################
##      TESTS FOR      ##
## ABSTRACT_BASE_MODEL ##
#########################


class AbstractSubclass(AbstractBaseModel):
    __tablename__ = "abstract_subclass"


abstract_object = AbstractSubclass(id=1)


def test_abstract_base_model_attributes_have_correct_sqlalchemy_types():
    assert type(AbstractSubclass.id.type) is Integer
    assert type(AbstractSubclass.created_at.type) is DateTime
    assert type(AbstractSubclass.last_updated.type) is DateTime


def test_abstract_base_model_has_fields_details_attributes():
    assert isinstance(abstract_object.fields, dict)
    assert isinstance(abstract_object.fieldtypes, dict)
    assert isinstance(abstract_object.fieldnames, set)
    assert isinstance(abstract_object.primary_keys, set)


def test_abstract_base_model_fields_attribute():
    expected_fields = {
        "id": AbstractSubclass.id,
        "created_at": AbstractSubclass.created_at,
        "last_updated": AbstractSubclass.last_updated,
    }
    assert expected_fields == abstract_object.fields


def test_abstract_base_model_fieldtypes_attribute():
    expected_fieldtypes = {
        "id": AbstractSubclass.id.type,
        "created_at": AbstractSubclass.created_at.type,
        "last_updated": AbstractSubclass.last_updated.type,
    }
    assert expected_fieldtypes == abstract_object.fieldtypes


def test_abstract_base_model_fieldnames_attribute():
    expected_fieldnames = {"id", "created_at", "last_updated"}
    assert abstract_object.fieldnames == expected_fieldnames


def test_abstract_base_model_primary_keys():
    expected_primary_keys = {"id"}
    assert abstract_object.primary_keys == expected_primary_keys


#########################
##      TESTS FOR      ##
##     REAL MODELS     ##
#########################


valid_user = MockModel(id=999, tg_id=10999)
valid_category = MockModel(
    id=999, name="test_category", type=CategoryType.EXPENSES, user_id=1
)
invalid_type_category = MockModel(
    id=999, name="test_category", type="invalid_type", user_id=1
)
valid_entry = MockModel(
    id=999,
    sum=9993991,
    transaction_date=now(),
    description="test",
    user_id=1,
    category_id=3,
)
entry_zero_sum = MockModel(
    id=999,
    sum=0,
    transaction_date=now(),
    category_id=1,
    user_id=1,
    description="test",
)
entry_without_user_id = MockModel(
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
    user_id=1,
    description="test",
)
entry_without_description = MockModel(
    id=999,
    sum=9993991,
    transaction_date=now(),
    user_id=1,
    category_id=3,
)


def test_user_class_has_expected_fields():
    expected_fieldnames = {
        "tg_id",
        "budget_currency",
        "is_active",
        "categories",
        "entries",
        "id",
        "created_at",
        "last_updated",
    }
    assert User.fieldnames == expected_fieldnames


def test_user_has_expected_str_representation(db_session, create_users):
    user = db_session.get(User, 1)
    expected_str = (
        f"User(Id={user.id}, TelegramId={user.tg_id}, "
        f"Currency={user.budget_currency}, IsActive={user.is_active})"
    )
    assert str(user) == expected_str
    assert repr(user) == expected_str


def test_user_create_with_valid_data_success(db_session, create_users):
    inital_user_count = db_session.query(User).count()

    db_session.add(User(**valid_user()))
    db_session.commit()

    from_db = db_session.get(User, valid_user.id)
    assert from_db.tg_id == valid_user.tg_id
    assert from_db.is_active is True
    assert from_db.is_anonymous is False
    assert from_db.categories == []
    assert from_db.entries == []
    assert from_db._datefield is User.created_at

    current_user_count = db_session.query(User).count()
    assert current_user_count == inital_user_count + 1


def test_create_user_without_currency_arg_sets_default(
    db_session, create_users
):
    default_currency = User.budget_currency.default.arg
    user = db_session.get(User, 1)
    assert user.budget_currency == default_currency


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


def test_user_add_category_appear_in_categories_attr(db_session, create_users):
    db_session.add(
        Category(id=999, name="test01", type=CategoryType.EXPENSES, user_id=1)
    )
    db_session.commit()

    assert db_session.get(User, 1).categories == [
        db_session.get(Category, 999)
    ]


def test_user_add_entry_appear_in_entries_attr(db_session, create_categories):
    db_session.add(Entry(id=999, sum=10000, user_id=1, category_id=1))
    db_session.commit()

    assert db_session.get(User, 1).entries == [db_session.get(Entry, 999)]


def test_category_model_has_expected_fields():
    expected_fieldnames = {
        "name",
        "type",
        "last_used",
        "user_id",
        "user",
        "entries",
        "num_entries",
        "id",
        "created_at",
        "last_updated",
    }
    assert Category.fieldnames == expected_fieldnames


def test_category_has_expected_str_representation(
    db_session, create_categories
):
    category = db_session.get(Category, 1)
    expected_str = (
        f"Category(Id={category.id}, Name={category.name}, "
        f"Type={category.type.value}, UserId={category.user_id}, "
        f"NumEntries={category.num_entries})"
    )

    from_db = db_session.get(Category, 1)
    assert str(from_db) == expected_str
    assert repr(from_db) == expected_str


def test_user_category_with_valid_data_success(db_session, create_users):
    inital_category_count = db_session.query(Category).count()

    db_session.add(Category(**valid_category()))
    db_session.commit()

    from_db = db_session.get(Category, valid_category.id)
    assert from_db.name == valid_category.name
    assert from_db.type == valid_category.type
    assert from_db.user_id == valid_category.user_id
    assert from_db.num_entries == 0
    assert from_db.entries == []
    assert from_db._datefield is Category.last_used

    current_category_count = db_session.query(Category).count()
    assert current_category_count == inital_category_count + 1


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_category_with_invalid_type_raises_error(db_session):
    db_session.add(Category(**invalid_type_category()))
    db_session.commit()


def test_category_sets_last_used_attr_to_default(
    db_session, create_categories
):
    import datetime as dt

    category = db_session.get(Category, 1)
    assert category.last_used == dt.datetime(year=1970, month=1, day=1)


def test_category_gets_deleted_when_user_deleted(
    db_session, create_categories
):
    user_id = 1
    intial_category_count = (
        db_session.query(Category).filter_by(user_id=user_id).count()
    )
    assert intial_category_count > 0

    db_session.query(User).filter_by(id=user_id).delete()
    db_session.commit()
    current_category_count = (
        db_session.query(Category).filter_by(user_id=user_id).count()
    )
    assert current_category_count == 0


def test_category_delete_success_if_no_entries_exist(
    db_session, create_categories
):
    db_session.query(Category).filter_by(id=1).delete()
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_category_delete_raise_error_if_entries_exist(
    db_session, create_entries
):
    db_session.query(Category).filter_by(id=1).delete()
    db_session.commit()


def test_category_render(db_session, create_categories):
    category = db_session.get(Category, 1)
    expected_str = (
        f"{category.name.capitalize()} ({category.type.description}), "
        f"{category.num_entries} операций"
    )
    assert category.render() == expected_str


def test_entry_model_has_expected_fields():
    expected_fieldnames = {
        "sum",
        "description",
        "transaction_date",
        "user_id",
        "category_id",
        "user",
        "category",
        "id",
        "created_at",
        "last_updated",
    }
    assert Entry.fieldnames == expected_fieldnames


def test_entry_has_expected_str_representation(db_session, create_entries):
    entry = db_session.get(Entry, 1)
    expected_str = (
        f"Entry(Id={entry.id}, Sum={entry._sum}, "
        f"Date={entry._transaction_date}, CategoryId={entry.category_id}, "
        f"UserId={entry.user_id}, Description={entry.description})"
    )

    assert str(entry) == expected_str
    assert repr(entry) == expected_str


def test_entry_create_with_valid_data_success(db_session, create_categories):
    inital_entry_count = db_session.query(Entry).count()

    db_session.add(Entry(**valid_entry()))
    db_session.commit()

    from_db = db_session.get(Entry, valid_entry.id)
    assert from_db.sum == valid_entry.sum
    assert from_db.description == valid_entry.description
    assert (
        from_db._transaction_date
        == f"{valid_entry.transaction_date:%Y-%m-%d %H:%M:%S}"
    )
    assert from_db.user_id == valid_entry.user_id
    assert from_db.category_id == valid_entry.category_id
    assert from_db._datefield is Entry.transaction_date
    assert from_db._cashflowfield is Entry.sum

    current_entry_count = db_session.query(Entry).count()
    assert current_entry_count == inital_entry_count + 1


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_entry_with_zero_sum_raises_error(db_session, create_entries):
    db_session.add(Entry(**entry_zero_sum()))
    db_session.commit()


@pytest.mark.xfail(raises=IntegrityError, strict=True)
def test_entry_without_budget_id_raises_error(db_session, create_entries):
    db_session.add(Entry(**entry_without_user_id()))
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
    assert entry.description is None


def test_entry_gets_deleted_when_user_deleted(db_session, create_entries):
    user_id = 1
    intial_entry_count = (
        db_session.query(Entry).filter_by(user_id=user_id).count()
    )
    assert intial_entry_count > 0

    db_session.query(User).filter_by(id=user_id).delete()
    db_session.commit()

    current_category_count = (
        db_session.query(Entry).filter_by(user_id=user_id).count()
    )
    assert current_category_count == 0


def test_entry_render(db_session, create_entries):
    entry = Entry(**valid_entry())
    db_session.add(entry)
    db_session.commit()

    user = db_session.get(User, entry.user_id)
    category = db_session.get(Category, entry.category_id)

    expected_str = (
        f"+{entry._sum} {user.budget_currency}, "
        f"{category.name}, {entry._transaction_date}, {entry.description}"
    )
    assert entry.render() == expected_str
