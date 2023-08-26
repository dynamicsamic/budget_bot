import pytest
from sqlalchemy.orm import Query

from app.db import exceptions
from app.db.managers import ModelManager
from app.utils import timed_tomorrow, timed_yesterday
from tests.conf import constants

from .fixtures import (
    GenericTestModel,
    create_tables,
    db_session,
    engine,
    generic_manager,
    populate_tables,
)


@pytest.mark.xfail(raises=exceptions.InvalidOrderByValue, strict=True)
def test_create_manager_with_invalid_type_order_by_raises_error():
    ModelManager(GenericTestModel, order_by=1)


@pytest.mark.xfail(raises=exceptions.InvalidOrderByValue, strict=True)
def test_create_manager_with_absent_model_filed_in_order_by_raises_error():
    ModelManager(GenericTestModel, order_by=["absent_field"])


@pytest.mark.xfail(raises=exceptions.InvalidFilter, strict=True)
def test_create_manager_with_invalid_type_filters_raises_error():
    ModelManager(GenericTestModel, filters=1)


@pytest.mark.xfail(raises=exceptions.InvalidFilter, strict=True)
def test_create_manager_with_invalid_filter_expression_raises_error():
    ModelManager(GenericTestModel, filters=["invalid_expression"])


@pytest.mark.xfail(raises=exceptions.InvalidFilter, strict=True)
def test_create_manager_with_absent_model_filed_in_filters_raises_error():
    ModelManager(GenericTestModel, filters=["absent_field=1"])


@pytest.mark.xfail(raises=exceptions.InvalidFilter, strict=True)
def test_create_manager_with_invalid_sign_in_filter_epression_raises_error():
    ModelManager(GenericTestModel, filters=["id===1"])


@pytest.mark.xfail(raises=exceptions.InvalidFilter, strict=True)
def test_create_manager_with_missing_value_in_filter_epression_raises_error():
    ModelManager(GenericTestModel, filters=["id=="])


@pytest.mark.xfail(raises=exceptions.InvalidDateField, strict=True)
def test_create_manager_with_absent_datefiled_raises_error():
    ModelManager(GenericTestModel, datefield="absent_field")


@pytest.mark.xfail(raises=exceptions.InvalidDateField, strict=True)
def test_create_manager_with_invalid_type_datefield_raises_error():
    ModelManager(GenericTestModel, datefield="id")


@pytest.mark.xfail(raises=exceptions.InvalidOrderByValue, strict=True)
def test_set_ivalid_order_by_raises_error(generic_manager):
    generic_manager.order_by = ["absent_field"]


@pytest.mark.xfail(raises=exceptions.InvalidFilter, strict=True)
def test_set_invalid_filter_expression_raises_error(generic_manager):
    generic_manager.filters = ["invalid_expression"]


@pytest.mark.xfail(raises=exceptions.InvalidDateField, strict=True)
def test_set_invalid_datefield_raises_error(generic_manager):
    generic_manager.datefield = "id"


def test_create_manager_without_session_flow(db_session):
    manager = ModelManager(GenericTestModel)
    assert isinstance(manager, ModelManager)
    assert manager.model is GenericTestModel
    assert manager.session is None

    # associate session with manager
    manager(db_session)

    assert manager.session is not None
    assert isinstance(manager.all(), Query)


def test_validate_filters_returns_filters_when_set_true():
    manager = ModelManager(GenericTestModel, filters=["id>1"])

    filters = manager._validate_filters(return_filters=True)
    assert isinstance(filters, list)


def test_set_default_order_by(generic_manager):
    generic_manager.order_by = ["name"]
    generic_manager._set_default_order_by()
    assert generic_manager.order_by == ["created_at", "id"]


def test_set_default_datefield(generic_manager):
    generic_manager.datefield = "custom_datefield"
    generic_manager._set_default_datefield()
    assert generic_manager.datefield == "created_at"


def test_reset_filters(generic_manager):
    generic_manager.filters = ["id>1"]
    generic_manager._reset_filters()
    generic_manager.filters == None


def test_update_with_valid_id_without_kwargs_return_false(generic_manager):
    assert generic_manager.update(1) == False


def test_update_with_unexisting_id_return_false(generic_manager):
    assert generic_manager.update(-1, name="test_obj") == False


def test_update_with_valid_id_with_valid_kwargs_return_true(
    generic_manager,
):
    updated = generic_manager.update(1, name="test_obj")
    assert isinstance(updated, bool)
    assert updated == True


def test_update_by_default_saves_changes_to_db(generic_manager):
    id_ = 1
    name = "test_obj"
    assert generic_manager.update(id_, name=name) == True
    assert generic_manager.get(id_).name == name


# fix this later
@pytest.mark.skip
def test_update_with_commit_false_does_not_save_changes_to_db(
    generic_manager,
):
    id_ = 1
    name = "test_obj"
    assert generic_manager.update(id_, commit=False, name=name) == True
    assert generic_manager.get(id_).name != name


def test_delete_with_valid_id_return_true(generic_manager):
    deleted = generic_manager.delete(1)
    assert isinstance(deleted, bool)
    assert deleted == True


def test_delete_with_unexisting_id_return_false(generic_manager):
    deleted = generic_manager.delete(-1)
    assert isinstance(deleted, bool)
    assert deleted == False


def test_delete_with_invalid_id_return_false(generic_manager):
    deleted = generic_manager.delete("hello")
    assert isinstance(deleted, bool)
    assert deleted == False


def test_get_with_valid_id_find_obj(generic_manager):
    id_ = 1
    obj = generic_manager.get(id_)
    assert isinstance(obj, GenericTestModel)
    assert obj.id == id_


def test_get_with_unexisting_id_return_none(generic_manager):
    assert generic_manager.get(-1) is None


def test_get_with_invalid_id_return_none(generic_manager):
    assert generic_manager.get("invalid") is None


def test_get_by_with_name_kwarg_find_obj_by_name(generic_manager):
    name = "obj1"
    obj = generic_manager.get_by(name=name)
    assert isinstance(obj, GenericTestModel)
    assert obj.name == name


def test_get_by_uses_several_kwargs_to_find_obj(generic_manager):
    id_ = 1
    name = "obj1"
    obj = generic_manager.get_by(id=id_, name=name)
    assert obj.id == id_
    assert obj.name == name


def test_get_by_with_unrelated_kwargs_return_none(generic_manager):
    first_obj_id = 1
    second_obj_name = "obj2"
    assert (
        generic_manager.get_by(id=first_obj_id, name=second_obj_name) is None
    )


def test_get_by_with_valid_kwarg_name_and_unexisting_kwarg_value_return_none(
    generic_manager,
):
    invalid_kwargs = {"name": "invalid"}
    assert generic_manager.get_by(**invalid_kwargs) is None


def test_get_by_with_invalid_kwarg_return_none(generic_manager):
    invalid_kwargs = {"invalid": "invalid"}
    assert generic_manager.get_by(**invalid_kwargs) is None


def test_get_by_without_kwargs_return_none(generic_manager):
    assert generic_manager.get_by() is None


def test_all_return_query_result(generic_manager):
    model_instances = generic_manager.all()
    assert isinstance(model_instances, Query)


def test_all_result_is_iterable_of_model_instances(generic_manager):
    model_instances = generic_manager.all()
    assert all(isinstance(obj, GenericTestModel) for obj in model_instances)


def test_all_return_query_in_ascending_order(generic_manager):
    objects = generic_manager.all()
    dates = [obj.created_at for obj in objects.all()]
    assert all([dates[i] < dates[i + 1] for i in range(len(dates) - 1)])


def test_all_with_reverse_arg_return_query_in_descending_order(
    generic_manager,
):
    objects = generic_manager.all(reverse=True)
    dates = [obj.created_at for obj in objects.all()]
    assert all([dates[i] > dates[i + 1] for i in range(len(dates) - 1)])


def test_list_return_result_in_list(generic_manager):
    model_instances = generic_manager.list()
    assert isinstance(model_instances, list)


def test_list_return_empty_list_for_empty_table(db_session):
    assert ModelManager(GenericTestModel, db_session).list() == []


def test_list_return_query_in_ascending_order(generic_manager):
    objects = generic_manager.list()
    dates = [obj.created_at for obj in objects]
    assert all([dates[i] < dates[i + 1] for i in range(len(dates) - 1)])


def test_list_with_reverse_arg_return_query_in_descending_order(
    generic_manager,
):
    objects = generic_manager.list(reverse=True)
    dates = [obj.created_at for obj in objects]
    assert all([dates[i] > dates[i + 1] for i in range(len(dates) - 1)])


def test_select_return_query_result(generic_manager):
    selection = generic_manager.select(filters=["id==1"])
    assert isinstance(selection, Query)


def test_select_return_filtered_result(generic_manager):
    selection = generic_manager.select(filters=["id<=2"])
    assert all(obj.id <= 2 for obj in selection)
    assert selection.count() == 2


def test_select_return_reverse_ordered_result(generic_manager):
    selection = generic_manager.select(filters=["id<=2"], reverse=True).all()
    assert selection[0].id > selection[1].id


def test_count_return_number_of_all_instances(generic_manager):
    num_entries = generic_manager.count()
    assert num_entries == constants["TEST_SAMPLE_SIZE"]
    assert isinstance(num_entries, int)


def test_exists_with_valid_id_return_true(generic_manager):
    exists = generic_manager.exists(1)
    assert isinstance(exists, bool)
    assert exists == True


def test_exists_with_unexisting_id_return_false(generic_manager):
    exists = generic_manager.exists(-1)
    assert isinstance(exists, bool)
    assert exists == False


def test_exists_with_invalid_id_return_false(generic_manager):
    exists = generic_manager.exists("hello")
    assert isinstance(exists, bool)
    assert exists == False


def test_first_return_first_added_instance(db_session, generic_manager):
    db_session.add(
        GenericTestModel(name="new_obj", created_at=timed_yesterday())
    )
    db_session.commit()

    first_from_db = generic_manager.first()
    assert isinstance(first_from_db, GenericTestModel)
    assert first_from_db.name == "new_obj"


def test_last_return_last_added_instance(db_session, generic_manager):
    db_session.add(
        GenericTestModel(name="new_obj", created_at=timed_tomorrow())
    )
    db_session.commit()

    last_from_db = generic_manager.last()
    assert isinstance(last_from_db, GenericTestModel)
    assert last_from_db.name == "new_obj"


def test_first_n_return_given_number_of_first_added_instances(
    db_session, generic_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            GenericTestModel(name=test_name, created_at=timed_yesterday())
            for test_name in test_names
        ]
    )
    db_session.commit()

    first_n_from_db = generic_manager.first_n(sample_size)
    assert isinstance(first_n_from_db, Query)

    first_n_from_db = first_n_from_db.all()
    assert len(first_n_from_db) == sample_size

    first_n_names = [obj.name for obj in first_n_from_db]
    assert first_n_names == test_names


def test_first_n_return_empty_result_for_zero_arg(generic_manager):
    first_n_from_db = generic_manager.first_n(0)
    assert isinstance(first_n_from_db, Query)
    assert first_n_from_db.all() == []


def test_last_n_return_given_number_of_last_added_instances(
    db_session, generic_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            GenericTestModel(name=test_name, created_at=timed_tomorrow())
            for test_name in test_names
        ]
    )
    db_session.commit()

    last_n_from_db = generic_manager.last_n(sample_size)
    assert isinstance(last_n_from_db, Query)

    last_n_from_db = last_n_from_db.all()
    assert len(last_n_from_db) == sample_size

    last_n_names = [obj.name for obj in last_n_from_db]
    assert last_n_names == list(reversed(test_names))


def test_last_n_return_empty_result_for_zero_arg(generic_manager):
    last_n_from_db = generic_manager.last_n(0)
    assert isinstance(last_n_from_db, Query)
    assert last_n_from_db.all() == []


def test_last_n_with_filters_return_filtered_result(
    db_session, generic_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            GenericTestModel(name=test_name, created_at=timed_tomorrow())
            for test_name in test_names
        ]
    )
    db_session.commit()

    last_n_filtered = generic_manager.last_n(
        sample_size, filters=["name==new_obj1"]
    )
    assert last_n_filtered.count() == 1
