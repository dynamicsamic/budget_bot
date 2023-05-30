from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app import settings
from app.db import prod_engine, test_engine


def session_agnostic(f):
    """Decorator that injects a sqlalchemy session into class method."""

    @wraps(f)
    def inner(self, *args, **kwargs):
        session_exists = False
        if args:
            for arg in args:
                if isinstance(arg, (Session, scoped_session)):
                    session_exists = True
        if not session_exists and kwargs:
            for kwarg_value in kwargs.values():
                if isinstance(kwarg_value, (Session, scoped_session)):
                    session_exists = True
        if session_exists:
            return f(self, *args, **kwargs)
        if hasattr(self, "db_engine") and self.db_engine is not None:
            session = scoped_session(sessionmaker(bind=self.db_engine))
        else:
            engine = test_engine if settings.DEBUG else prod_engine
            session = scoped_session(sessionmaker(bind=engine))
        kwargs["session"] = session
        return f(self, *args, **kwargs)

    return inner
