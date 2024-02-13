from sqlalchemy.orm import Session, scoped_session

from app.db import db_session


def foo():
    with db_session() as session:
        # session.close()
        session.connection().close()
        yield session
    session.close()
    session.connection().close()


def test_db_session_with_new_session(create_test_tables):
    with db_session() as session:
        ...

    assert isinstance(session, (scoped_session, Session))
    assert session.is_active


def test_db_session_reuse_existing_session(
    create_test_tables, persistent_db_session
):
    with db_session(existing_session=persistent_db_session) as session:
        ...

    assert session is persistent_db_session
