from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app import settings

prod_engine = create_engine(
    settings.DATABASE["prod_db_url"], echo=settings.DEBUG
)
test_engine = create_engine(
    settings.DATABASE["test_real_db_url"], echo=settings.DEBUG
)
inmemory_test_engine = create_engine(
    settings.DATABASE["test_mem_db_url"], echo=settings.DEBUG
)


@contextmanager
def db_session(engine: Engine = test_engine):
    Session = scoped_session(sessionmaker(bind=engine))
    try:
        yield Session
    except Exception:
        Session.rollback()
    finally:
        Session.close()
