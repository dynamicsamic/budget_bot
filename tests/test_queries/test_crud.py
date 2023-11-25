from sqlalchemy.orm import Query

from app.db.queries import crud
from app.utils import now

from .conftest import BaseTestModel


def test_create_with_valid_args_return_new_instance(db_session):
    valid_args = {"id": 999999, "name": "new_user", "created_at": now()}
    obj = crud.create(BaseTestModel, db_session, **valid_args)
    assert isinstance(obj, BaseTestModel)
    assert obj.id == valid_args["id"]
    assert obj.name == valid_args["name"]


def test_create_with_missing_or_invalid_model_attribute_return_none(
    db_session,
):
    assert crud.create(BaseTestModel, db_session, id=999999) is None
    assert (
        crud.create(BaseTestModel, db_session, id=999999, invalid="invalid")
        is None
    )
    assert (
        crud.create(BaseTestModel, db_session, id=999999, name=["invalid"])
        is None
    )


def test_create_with_existing_id_return_none(
    db_session, populate_generic_table
):
    obj = crud.get(BaseTestModel, db_session, [BaseTestModel.id == 1])
    assert (
        crud.create(
            BaseTestModel, db_session, id=obj.id, name="most_recent_obj"
        )
        is None
    )


def test_update_with_unexisting_id_return_false(
    db_session, populate_generic_table
):
    assert (
        crud.update(BaseTestModel, db_session, -1, {"name": "test_obj"})
        is False
    )


def test_update_with_valid_id_with_valid_kwargs_return_true(
    db_session,
    populate_generic_table,
):
    updated = crud.update(BaseTestModel, db_session, 1, {"name": "test_obj"})
    assert isinstance(updated, bool)
    assert updated is True


def test_update_saves_changes_to_db(db_session, populate_generic_table):
    id_ = 1
    name = "test_obj"
    assert crud.update(BaseTestModel, db_session, id_, {"name": name}) is True
    assert (
        crud.get(BaseTestModel, db_session, [BaseTestModel.id == id_]).name
        == name
    )


def test_delete_with_valid_id_return_true(db_session, populate_generic_table):
    deleted = crud.delete(BaseTestModel, db_session, 1)
    assert isinstance(deleted, bool)
    assert deleted is True


def test_delete_with_unexisting_id_return_false(
    db_session, populate_generic_table
):
    deleted = crud.delete(BaseTestModel, db_session, -1)
    assert isinstance(deleted, bool)
    assert deleted is False


def test_delete_with_invalid_id_return_false(
    db_session, populate_generic_table
):
    deleted = crud.delete(BaseTestModel, db_session, "hello")
    assert isinstance(deleted, bool)
    assert deleted is False


def test_get_with_valid_id_find_obj(db_session, populate_generic_table):
    id_ = 1
    obj = crud.get(BaseTestModel, db_session, [BaseTestModel.id == id_])
    assert isinstance(obj, BaseTestModel)
    assert obj.id == id_


def test_get_with_unexisting_id_return_none(
    db_session, populate_generic_table
):
    assert (
        crud.get(BaseTestModel, db_session, [BaseTestModel.id == -1]) is None
    )


def test_get_with_invalid_id_return_none(db_session, populate_generic_table):
    assert (
        crud.get(BaseTestModel, db_session, [BaseTestModel.id == "invalid"])
        is None
    )


def test_get_with_name_kwarg_find_obj_by_name(
    db_session, populate_generic_table
):
    name = "obj1"
    obj = crud.get(BaseTestModel, db_session, [BaseTestModel.name == name])
    assert isinstance(obj, BaseTestModel)
    assert obj.name == name


def test_get_uses_several_kwargs_to_find_obj(
    db_session, populate_generic_table
):
    id_ = 1
    name = "obj1"
    obj = crud.get(
        BaseTestModel,
        db_session,
        [BaseTestModel.id == id_, BaseTestModel.name == name],
    )
    assert obj.id == id_
    assert obj.name == name


def test_get_with_unrelated_kwargs_return_none(
    db_session, populate_generic_table
):
    first_obj_id = 1
    second_obj_name = "obj2"
    assert (
        crud.get(
            BaseTestModel,
            db_session,
            [
                BaseTestModel.id == first_obj_id,
                BaseTestModel.name == second_obj_name,
            ],
        )
        is None
    )


def test_get_all_return_query_result(db_session, populate_generic_table):
    model_instances = crud.get_all(BaseTestModel, db_session)
    assert isinstance(model_instances, Query)


def test_get_all_result_is_iterable_of_model_instances(
    db_session, populate_generic_table
):
    model_instances = crud.get_all(BaseTestModel, db_session)
    assert all(isinstance(obj, BaseTestModel) for obj in model_instances)


def test_get_all_return_query_in_ascending_order_by_default(
    db_session, populate_generic_table
):
    objects = crud.get_all(BaseTestModel, db_session)
    dates = [obj.created_at for obj in objects.all()]
    assert all([dates[i] < dates[i + 1] for i in range(len(dates) - 1)])


def test_get_all_may_return_query_in_descending_order(
    db_session,
    populate_generic_table,
):
    objects = crud.get_all(
        BaseTestModel, db_session, [BaseTestModel.created_at.desc()]
    )
    dates = [obj.created_at for obj in objects.all()]
    assert all([dates[i] > dates[i + 1] for i in range(len(dates) - 1)])
