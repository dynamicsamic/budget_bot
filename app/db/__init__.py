import logging
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app import settings
from app.utils import aiogram_log_handler

logger = logging.getLogger(__name__)
logger.addHandler(aiogram_log_handler)

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
def db_session(
    engine: Engine = test_engine,
    *,
    existing_session: scoped_session | Session = None,
):
    if (
        isinstance(existing_session, (scoped_session, Session))
        and existing_session.is_active
    ):
        session = existing_session
        logger.info("reuse existing db_session")
    else:
        session = scoped_session(sessionmaker(bind=engine))
        logger.info("create new db_session")

    try:
        yield session
    except Exception as e:
        logger.exception(f"db session interupted with exception: {e}")
        session.rollback()
        raise e
    finally:
        session.close()
        logger.info("db_session closed")
