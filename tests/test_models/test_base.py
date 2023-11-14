from sqlalchemy import DateTime, Integer

from .fixtures import (
    AbstractSubclass,
    create_fake_test_objects,
    create_tables,
    db_session,
    engine,
)


def test_abstract_base_model_subclass_attributes_have_correct_sqlalchemy_types(
    db_session, create_fake_test_objects
):
    assert type(AbstractSubclass.id.type) is Integer
    assert type(AbstractSubclass.created_at.type) is DateTime
    assert type(AbstractSubclass.last_updated.type) is DateTime
