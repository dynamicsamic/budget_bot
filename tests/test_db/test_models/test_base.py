from sqlalchemy import DateTime, Integer

from app.db.models.base import AbstractBaseModel


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
