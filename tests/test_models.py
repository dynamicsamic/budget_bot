from sqlalchemy import func, select

from db import models

from .fixtures import db_session, test_user, user_data


def test_db_creates_user_with_provided_data(db_session, test_user):
    db_session.add(test_user)
    db_session.commit()
    queryset = db_session.execute(
        select(models.User).where(
            models.User.tg_id == user_data["test_user"]["tg_id"]
        )
    )
    user = queryset.scalar()
    assert user.tg_username == user_data["test_user"]["tg_username"]


def test_another(db_session):
    print(db_session.execute(select(func.count(models.User.id))))
