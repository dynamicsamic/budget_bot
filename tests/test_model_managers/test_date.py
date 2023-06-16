import datetime as dt

import pytest

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
    db_session.add(TestModel(name="new_obj", created_at=yesterday()))
    db_session.commit()

    first_from_db = date_manager.first()
    assert isinstance(first_from_db, TestModel)
    assert first_from_db.name == "new_obj"


def test_last_method_return_last_added_instance(db_session, date_manager):
    db_session.add(TestModel(name="new_obj", created_at=tomorrow()))
    db_session.commit()

    last_from_db = date_manager.last()
    assert isinstance(last_from_db, TestModel)
    assert last_from_db.name == "new_obj"


@pytest.mark.current
def test_first_n_return_given_number_of_first_added_instances(
    db_session, date_manager
):
    db_session.add_all(
        [
            TestModel(name=f"new_obj{i}", created_at=tomorrow())
            for i in range(5)
        ]
    )
    db_session.commit()

    sample_size = 5
    first_n_from_db = date_manager.first_n(sample_size)
    assert len(list(first_n_from_db)) == sample_size
    print(type(date_manager.first_n(0)))
