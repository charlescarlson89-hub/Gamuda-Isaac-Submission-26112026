"""Prepare pgAdmin SQL; optionally create only the dedicated test database.

Run from backend: .venv/Scripts/python.exe scripts/create_database.py [--execute]
Set ADMIN_DATABASE_URL in the ignored backend/.env to enable --execute.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.engine import make_url

from app.config import BACKEND_ROOT, get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    app_url = make_url(settings.database_url.get_secret_value())
    if app_url.database != "soilsync_remake_test" or not app_url.username:
        raise SystemExit("Setup is restricted to the soilsync_remake_test database.")
    quote = dialect().identifier_preparer.quote
    statement = f"CREATE DATABASE {quote(app_url.database)} OWNER {quote(app_url.username)}"
    output = BACKEND_ROOT / "sql" / "000_create_database.sql"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "-- In pgAdmin, connect Query Tool to the postgres database as an administrator.\n"
        "-- Run this statement once with Auto-commit enabled. Do not run inside BEGIN.\n"
        "-- Existing SoilSync databases are not changed.\n" + statement + ";\n",
        encoding="utf-8",
    )
    print(f"Prepared {output.name} for pgAdmin.")
    if not args.execute:
        return
    admin_url = settings.admin_database_url.get_secret_value()
    if not admin_url:
        raise SystemExit(
            "Set ADMIN_DATABASE_URL locally in backend/.env, or run the SQL in pgAdmin."
        )
    admin = make_url(admin_url)
    if (admin.host, admin.port) != (app_url.host, app_url.port):
        raise SystemExit("Administrator and app connections must point to the same server.")
    engine = create_engine(admin, isolation_level="AUTOCOMMIT", hide_parameters=True)
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": app_url.database}
            ).scalar()
            if exists:
                print("Test database already exists; retained without changes.")
            else:
                conn.exec_driver_sql(statement)
                print("Created the separate soilsync_remake_test database.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
