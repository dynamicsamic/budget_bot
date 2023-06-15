import datetime as dt

from app import settings
from app.utils import today, tomorrow, yesterday

from .fixtures import (
    TestModel,
    create_tables,
    date_manager,
    db_session,
    engine,
    populate_db,
)


def test_first_method_return_first_added_instance(db_session, date_manager):
    db_session.add(TestModel(name="new_user", created_at=yesterday()))
    db_session.commit()

    first_from_db = date_manager.first()
    assert isinstance(first_from_db, TestModel)
    assert first_from_db.name == "new_user"


def test_last_method_return_last_added_instance(db_session, date_manager):
    db_session.add(TestModel(name="new_user", created_at=tomorrow()))
    db_session.commit()

    last_from_db = date_manager.last()
    assert isinstance(last_from_db, TestModel)
    assert last_from_db.name == "new_user"
