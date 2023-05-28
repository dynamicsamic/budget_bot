from sqlalchemy import create_engine

from app import settings

prod_engine = create_engine(
    settings.DATABASE["prod_db_url"], echo=settings.DEBUG
)
test_engine = create_engine(
    settings.DATABASE["test_db_url"], echo=settings.DEBUG
)
