"""Export only the dedicated, synthetic test database as pgAdmin seed SQL."""

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.config import BACKEND_ROOT, get_settings
from app.database import session_factory
from app.models import Base


def literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (dict, list)):
        return "'" + json.dumps(value, ensure_ascii=False).replace("'", "''") + "'::jsonb"
    if isinstance(value, (date, datetime)):
        value = value.isoformat()
    return "'" + str(value).replace("'", "''") + "'"


settings = get_settings()
if (
    settings.app_env == "production"
    or make_url(settings.database_url.get_secret_value()).database != "soilsync_remake_test"
):
    raise SystemExit("Seed export is restricted to the dedicated test database.")
lines = [
    "-- SYNTHETIC TEST DATA ONLY. No real users, partner vouchers or live AI results.\n-- Run after 001_schema.sql inside soilsync_remake_test.\n-- Run scripts/seed.py --mock afterward to generate local mock proof images.\nBEGIN;\n"
]
with session_factory()() as db:
    # Refuse to export any real account that may have been created during testing.
    from app.models import User

    users = list(db.scalars(select(User)))
    if len(users) != 20 or any(not user.email.endswith("@soilsync.example") for user in users):
        raise SystemExit(
            "Export stopped: this database now contains non-seed accounts. Use the original generated seed SQL."
        )
    for table in Base.metadata.sorted_tables:
        rows = db.execute(select(table).order_by(table.c.id)).mappings().all()
        lines.append(f"-- {table.name}: {len(rows)} rows")
        columns = ", ".join('"' + column.name + '"' for column in table.columns)
        for row in rows:
            values = ", ".join(literal(row[column.name]) for column in table.columns)
            lines.append(
                f'INSERT INTO "{table.name}" ({columns}) VALUES ({values}) ON CONFLICT DO NOTHING;'
            )
        lines.append(
            f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {table.name};\n"
        )
lines.append("COMMIT;\n")
output = BACKEND_ROOT / "sql/002_mock_data.sql"
output.write_text("\n".join(lines), encoding="utf-8")
print(f"Exported {output.name} with synthetic records only.")
