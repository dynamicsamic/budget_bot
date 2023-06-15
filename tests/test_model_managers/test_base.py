import pytest
from sqlalchemy import select
from sqlalchemy.engine.result import ScalarResult

from app.db.managers import BaseModelManager
from tests.conf import constants

from .fixtures import (
    TestModel,
    base_manager,
    create_tables,
    db_session,
    engine,
    populate_db,
)


def test_get_method_with_valid_id_find_obj(base_manager):
    id_ = 1
    obj = base_manager.get(id_)
    assert isinstance(obj, TestModel)
    assert obj.id == id_


def test_get_method_with_unexisting_id_return_none(base_manager):
    assert base_manager.get(-1) is None


def test_get_method_with_invalid_id_return_none(base_manager):
    assert base_manager.get("invalid") is None


def test_get_by_method_with_name_kwarg_find_obj_by_name(base_manager):
    name = "obj1"
    obj = base_manager.get_by(name=name)
    assert isinstance(obj, TestModel)
    assert obj.name == name


def test_get_by_method_uses_several_kwargs_to_find_obj(base_manager):
    id_ = 1
    name = "obj1"
    obj = base_manager.get_by(id=id_, name=name)
    assert obj.id == id_
    assert obj.name == name


def test_get_by_method_with_unrelated_kwargs_return_none(base_manager):
    first_obj_id = 1
    second_obj_name = "obj2"
    assert base_manager.get_by(id=first_obj_id, name=second_obj_name) is None


def test_get_by_method_with_valid_kwarg_name_and_unexisting_kwarg_value_return_none(
    base_manager,
):
    invalid_kwargs = {"name": "invalid"}
    assert base_manager.get_by(**invalid_kwargs) is None


def test_get_by_method_with_invalid_kwarg_return_none(base_manager):
    invalid_kwargs = {"invalid": "invalid"}
    assert base_manager.get_by(**invalid_kwargs) is None


def test_get_by_method_without_kwargs_return_none(base_manager):
    assert base_manager.get_by() is None


def test_all_method_without_args_return_scalar_result(base_manager):
    model_instances = base_manager.all()
    assert isinstance(model_instances, ScalarResult)


def test_all_method_without_args_result_is_iterable(base_manager):
    model_instances = base_manager.all()
    assert all(isinstance(obj, TestModel) for obj in model_instances)


def test_all_method_with_to_list_arg_return_list(base_manager):
    model_instances = base_manager.all(to_list=True)
    assert isinstance(model_instances, list)


def test_all_method_return_empty_list_for_empty_table(db_session):
    assert BaseModelManager(TestModel, db_session).all(to_list=True) == []


def test_update_method_with_valid_id_without_kwargs_return_false(base_manager):
    assert base_manager.update(1) == False


def test_update_method_with_unexisting_id_return_false(base_manager):
    assert base_manager.update(-1, name="test_obj") == False


def test_update_method_with_valid_id_with_valid_kwargs_return_true(
    base_manager,
):
    updated = base_manager.update(1, name="test_obj")
    assert isinstance(updated, bool)
    assert updated == True


def test_update_method_by_default_saves_changes_to_db(base_manager):
    id_ = 1
    name = "test_obj"
    assert base_manager.update(id_, name=name) == True
    assert base_manager.get(id_).name == name


# fix this later
@pytest.mark.skip
def test_update_method_with_commit_false_does_not_save_changes_to_db(
    base_manager,
):
    id_ = 1
    name = "test_obj"
    assert base_manager.update(id_, commit=False, name=name) == True
    assert base_manager.get(id_).name != name


def test_delete_method_with_valid_id_return_true(base_manager):
    deleted = base_manager.delete(1)
    assert isinstance(deleted, bool)
    assert deleted == True


def test_delete_method_with_unexisting_id_return_false(base_manager):
    deleted = base_manager.delete(-1)
    assert isinstance(deleted, bool)
    assert deleted == False


def test_delete_method_with_invalid_id_return_false(base_manager):
    deleted = base_manager.delete("hello")
    assert isinstance(deleted, bool)
    assert deleted == False


def test_count_method_return_number_of_all_instances(base_manager):
    num_entries = base_manager.count()
    assert num_entries == constants["TEST_SAMPLE_SIZE"]
    assert isinstance(num_entries, int)


def test_exists_method_with_valid_id_return_true(base_manager):
    exists = base_manager.exists(1)
    assert isinstance(exists, bool)
    assert exists == True


def test_exists_method_with_unexisting_id_return_false(base_manager):
    exists = base_manager.exists(-1)
    assert isinstance(exists, bool)
    assert exists == False


def test_exists_method_with_invalid_id_return_false(base_manager):
    exists = base_manager.exists("hello")
    assert isinstance(exists, bool)
    assert exists == False
