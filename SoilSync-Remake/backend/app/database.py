"""Database engine and request-scoped transactions."""

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings


@lru_cache
def session_factory():
    url = get_settings().database_url.get_secret_value()
    if not url:
        raise RuntimeError("Configure DATABASE_URL in your private SoilSyncRemake .env.")

    options = {"pool_pre_ping": True, "hide_parameters": True}

    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    else:
        options["connect_args"] = {"connect_timeout": 5}
        options.update(pool_size=5, max_overflow=5, pool_timeout=10)

    engine = create_engine(url, **options)
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with session_factory()() as db:
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise