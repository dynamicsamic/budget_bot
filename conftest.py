import pytest
from sqlalchemy import create_engine


@pytest.fixture(scope="session")
def inmemory_engine():
    return create_engine("sqlite://", echo=True)
