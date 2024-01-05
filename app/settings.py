from pathlib import Path

from pytz import timezone

ROOT_DIR = Path(__name__).resolve().parent
TIME_ZONE = timezone("Europe/Moscow")
DEBUG = True
DATABASE = {
    "prod_db_url": f"sqlite:///{ROOT_DIR}/db/prod.sqlite3",
    "test_real_db_url": f"sqlite:///{ROOT_DIR}/tests/test_data/test.sqlite3",
    "test_mem_db_url": "sqlite://",
}
