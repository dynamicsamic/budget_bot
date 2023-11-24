from sqlalchemy.orm import Session, scoped_session

from app.db.models import User
from app.db.queries.crud import get


def get_user(
    db_session: Session | scoped_session, *, user_id: int = 0, tg_id: int = 0
) -> User:
    if not (user_id or tg_id):
        raise ValueError(
            "Provide either a `user_id` or `tg_id` argument for get_user."
        )

    if user_id:
        return get(
            model=User, session=db_session, filters=[User.id == user_id]
        )
    return get(model=User, session=db_session, filters=[User.tg_id == tg_id])
