"""Load reference data and optionally 20 synthetic accounts into the test DB."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from app.config import get_settings
from app.database import session_factory
from app.models import Base
from app.seed_data import ensure_mock_photos, populate_catalogue, populate_mock_accounts

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--mock", action="store_true")
args = parser.parse_args()
settings = get_settings()
if args.mock and (
    settings.app_env == "production"
    or make_url(settings.database_url.get_secret_value()).database != "soilsync_remake_test"
):
    raise SystemExit("Mock accounts are restricted to soilsync_remake_test outside production.")
with session_factory()() as db, db.begin():
    populate_catalogue(db)
    if args.mock:
        populate_mock_accounts(db)
        ensure_mock_photos(db)
with session_factory()() as db:
    for table in Base.metadata.sorted_tables:
        print(f"{table.name}: {db.scalar(select(func.count()).select_from(table))}")
