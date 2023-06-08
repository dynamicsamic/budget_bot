import pytest
from sqlalchemy.engine.result import ScalarResult

from .conf import constants
from .fixtures import (
    TestModel,
    create_tables,
    db_session,
    engine,
    populate_db,
    test_manager,
)


def test_count_method_return_number_of_all_instances(test_manager):
    num_entries = test_manager.count()
    assert num_entries == constants["TEST_SAMPLE_SIZE"]
    assert isinstance(num_entries, int)


def test_all_method_without_args_return_scalar_result(test_manager):
    model_instances = test_manager.all()
    assert isinstance(model_instances, ScalarResult)


def test_all_method_with_to_list_arg_return_list(test_manager):
    model_instances = test_manager.all(to_list=True)
    assert isinstance(model_instances, list)


def test_get_method_with_valid_id_find_obj(test_manager):
    id_ = 1
    obj = test_manager.get(id_)
    assert isinstance(obj, TestModel)
    assert obj.id == id_


def test_get_method_with_unexisting_id_return_none(test_manager):
    assert test_manager.get(-1) is None


def test_get_method_with_invalid_id_return_none(test_manager):
    assert test_manager.get("invalid") is None


def test_get_by_method_with_name_kwarg_find_obj_by_name(test_manager):
    name = "obj1"
    obj = test_manager.get_by(name=name)
    assert isinstance(obj, TestModel)
    assert obj.name == name


def test_get_by_method_uses_several_kwargs_to_find_obj(test_manager):
    id_ = 1
    name = "obj1"
    obj = test_manager.get_by(id=id_, name=name)
    assert obj.id == id_
    assert obj.name == name


def test_get_by_method_with_unrelated_kwargs_return_none(test_manager):
    first_obj_id = 1
    second_obj_name = "obj2"
    assert test_manager.get_by(id=first_obj_id, name=second_obj_name) is None


def test_get_by_method_with_valid_kwarg_name_and_unexisting_kwarg_value_return_none(
    test_manager,
):
    invalid_kwargs = {"name": "invalid"}
    assert test_manager.get_by(**invalid_kwargs) is None


def test_get_by_method_with_invalid_kwarg_return_none(test_manager):
    invalid_kwargs = {"invalid": "invalid"}
    assert test_manager.get_by(**invalid_kwargs) is None


def test_get_method_without_kwargs_return_none(test_manager):
    assert test_manager.get_by() == None
