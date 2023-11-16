from sqlalchemy import DateTime, Integer

from .fixtures import (
    AbstractSubclass,
    abstract_object,
    create_tables,
    db_session,
    engine,
)


def test_abstract_base_model_attributes_have_correct_sqlalchemy_types():
    assert type(AbstractSubclass.id.type) is Integer
    assert type(AbstractSubclass.created_at.type) is DateTime
    assert type(AbstractSubclass.last_updated.type) is DateTime


def test_abstract_base_model_has_fields_details_attributes(
    abstract_object,
):
    obj = abstract_object

    assert isinstance(obj.fields, dict)
    assert isinstance(obj.fieldtypes, dict)
    assert isinstance(obj.fieldnames, set)
    assert isinstance(obj.primary_keys, set)


def test_abstract_base_model_fields_attribute(abstract_object):
    obj = abstract_object

    expected_fields = {
        "id": AbstractSubclass.id,
        "created_at": AbstractSubclass.created_at,
        "last_updated": AbstractSubclass.last_updated,
    }
    assert expected_fields == obj.fields


def test_abstract_base_model_fieldtypes_attribute(abstract_object):
    obj = abstract_object

    expected_fieldtypes = {
        "id": AbstractSubclass.id.type,
        "created_at": AbstractSubclass.created_at.type,
        "last_updated": AbstractSubclass.last_updated.type,
    }
    assert expected_fieldtypes == obj.fieldtypes


def test_abstract_base_model_fieldnames_attribute(abstract_object):
    obj = abstract_object

    expected_fieldnames = {"id", "created_at", "last_updated"}
    assert obj.fieldnames == expected_fieldnames


def test_abstract_base_model_primary_keys(abstract_object):
    obj = abstract_object

    expected_primary_keys = {"id"}
    assert obj.primary_keys == expected_primary_keys
