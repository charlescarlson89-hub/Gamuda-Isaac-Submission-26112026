"""Export PostgreSQL DDL and DBML from the same SQLAlchemy metadata."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import Boolean, CheckConstraint, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateIndex, CreateTable

from app.config import BACKEND_ROOT
from app.models import Base

TABLE_NOTES = {
    "users": "Registered accounts, consent and current EcoPoints balance. Admin access is configured outside the database.",
    "user_settings": "At most one preferences record per account.",
    "auth_sessions": "Revocable login sessions. Store only a SHA-256 token digest, never the raw session token.",
    "daily_checkins": "One daily check-in per user and Kuala Lumpur calendar date.",
    "waste_types": "Shared waste catalogue. The seeded Banana peels record has ID 1.",
    "scan_logs": "AI scan results and image hashes. A null waste_type_id represents an unmatched scan. Full item detections are stored in result.",
    "fertilizer_types": "Shared compost recipe catalogue. Completion days are planning estimates, not proof of maturity.",
    "waste_fertilizer_matches": "Many-to-many mapping between supported waste materials and compost recipes.",
    "plants": "Shared plant catalogue used by recipe guidance.",
    "fertilizer_suitable_plants": "Recipe-to-plant guidance. is_recommended=false marks an avoid relationship.",
    "fertilizer_recipe_steps": "Ordered instructions for a recipe.",
    "fertilizer_maintenance_guides": "At most one maintenance guide per recipe. Temperature and moisture are guidance, not camera measurements.",
    "batches": "Multiple batches per user. Progress measures three approved check-ins, not compost maturity.",
    "weekly_checkin_quests": "Three ordered photo quests per batch. FastAPI checks ownership, AI approval and photo reuse across the account. No seven-day waiting period is enforced.",
    "rewards": "Reward catalogue. Current partner items are prototype concepts; physical fulfilment is not implemented.",
    "reward_claims": "Claim records with debit snapshots. FastAPI checks the balance and saves the debit and claim in one transaction.",
    "points_ledger": "Append-only API accounting events. Unique event keys prevent duplicate point awards and debits.",
}

COLUMN_NOTES = {
    ("weekly_checkin_quests", "photo_data"): "Optional private JPEG bytes for hosted PostgreSQL storage. Never included in JSON responses; served only through the ownership-checked photo endpoint.",
    ("users", "password"): "Argon2 password hash, never plaintext.",
    (
        "users",
        "consented_at",
    ): "UTC-aware timestamp supplied by the application; no database-side default.",
    (
        "scan_logs",
        "provider",
    ): "The application default is gemini; there is no database-side default.",
    (
        "scan_logs",
        "image_sha256",
    ): "SHA-256 of the original scan file for per-user duplicate protection.",
    (
        "scan_logs",
        "result",
    ): "Structured AI result including detected items, confidence and catalogue matches.",
    (
        "weekly_checkin_quests",
        "storage_key",
    ): "Private storage object reference; image_proof_url is served through an ownership-checked API.",
    (
        "weekly_checkin_quests",
        "image_sha256",
    ): "SHA-256 of the normalised proof image. The API also checks reuse across this user's batches.",
    (
        "weekly_checkin_quests",
        "verification",
    ): "Visual compost approval evidence; nullable for legacy/mock proof. Not maturity certification.",
    (
        "points_ledger",
        "points",
    ): "Positive for earnings, negative for spending. Amounts are controlled by FastAPI.",
}

TABLE_GROUPS = {
    "Accounts": ["users", "user_settings", "auth_sessions", "daily_checkins"],
    "Waste_and_AI": ["waste_types", "scan_logs"],
    "Recipes_and_plants": [
        "fertilizer_types",
        "waste_fertilizer_matches",
        "plants",
        "fertilizer_suitable_plants",
        "fertilizer_recipe_steps",
        "fertilizer_maintenance_guides",
    ],
    "Batch_progress": ["batches", "weekly_checkin_quests"],
    "Rewards_and_points": ["rewards", "reward_claims", "points_ledger"],
}


def dbml_string(value):
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def dbml_default(column, pg):
    """Export actual server defaults, not Python-only ORM defaults."""
    if column.server_default is None:
        return None
    arg = column.server_default.arg
    if isinstance(arg, str):
        if isinstance(column.type, Boolean):
            return arg.lower()
        if isinstance(column.type, Integer):
            return str(int(arg))
        if isinstance(column.type, String):
            return dbml_string(arg)
    expression = str(arg.compile(dialect=pg)) if hasattr(arg, "compile") else str(arg)
    return "`" + expression + "`"


def render_dbml():
    pg = dialect()
    tables = Base.metadata.sorted_tables
    dbml = [
        "// Generated from backend/app/models.py. Paste this entire file into dbdiagram.io.\n"
        "// Regenerate without changing SQL migrations: python scripts/export_schema.py --dbml-only\n"
        "// This describes the application schema, not an independently verified Neon deployment.\n"
        "Project SoilSyncRemake {\n"
        "  database_type: 'PostgreSQL'\n"
        f"  Note: 'SoilSync by TEDA BYTE. FastAPI application schema with {len(tables)} tables. PostgreSQL may run locally or on Neon; pgAdmin is the management client. API ownership and AI rules supplement database constraints.'\n"
        "}\n"
    ]
    references = []
    for table in tables:
        dbml.append(f"Table {table.name} {{")
        for column in table.columns:
            column_type = (
                str(column.type.compile(dialect=pg))
                .lower()
                .replace("timestamp with time zone", "timestamptz")
            )
            options = []
            if column.primary_key:
                options.append("pk")
                if isinstance(column.type, Integer):
                    options.append("increment")
            if not column.nullable:
                options.append("not null")
            if column.unique:
                options.append("unique")
            default = dbml_default(column, pg)
            if default is not None:
                options.append(f"default: {default}")
            note = COLUMN_NOTES.get((table.name, column.name))
            if note:
                options.append(f"note: {dbml_string(note)}")
            settings = " [" + ", ".join(options) + "]" if options else ""
            dbml.append(f"  {column.name} {column_type}{settings}")
            for foreign_key in sorted(column.foreign_keys, key=lambda item: item.target_fullname):
                child = f"{table.name}.{column.name}"
                parent = foreign_key.target_fullname
                # In DBML's standalone one-to-one syntax the SECOND column is the FK.
                relationship = f"{parent} - {child}" if column.unique else f"{child} > {parent}"
                references.append(
                    f"Ref: {relationship}"
                    + (f" [delete: {foreign_key.ondelete.lower()}]" if foreign_key.ondelete else "")
                )
        unique_groups = sorted(
            (
                item
                for item in table.constraints
                if isinstance(item, UniqueConstraint) and len(item.columns) > 1
            ),
            key=lambda item: tuple(item.columns.keys()),
        )
        indexes = sorted(table.indexes, key=lambda item: item.name)
        if unique_groups or indexes:
            dbml.append("\n  indexes {")
            for constraint in unique_groups:
                settings = ["unique"]
                if constraint.name:
                    settings.append(f"name: {dbml_string(constraint.name)}")
                dbml.append(
                    "    ("
                    + ", ".join(constraint.columns.keys())
                    + ") ["
                    + ", ".join(settings)
                    + "]"
                )
            for index in indexes:
                expressions = [
                    expr.name
                    if getattr(expr, "table", None) is table
                    else "`" + str(expr.compile(dialect=pg)).replace(table.name + ".", "") + "`"
                    for expr in index.expressions
                ]
                settings = (["unique"] if index.unique else []) + [
                    f"name: {dbml_string(index.name)}"
                ]
                dbml.append("    (" + ", ".join(expressions) + ") [" + ", ".join(settings) + "]")
            dbml.append("  }")
        checks = sorted(
            (item for item in table.constraints if isinstance(item, CheckConstraint)),
            key=lambda item: str(item.sqltext),
        )
        if checks:
            dbml.append("\n  checks {")
            for constraint in checks:
                settings = f" [name: {dbml_string(constraint.name)}]" if constraint.name else ""
                dbml.append(f"    `{constraint.sqltext}`{settings}")
            dbml.append("  }")
        if table.name in TABLE_NOTES:
            dbml.append(f"\n  Note: {dbml_string(TABLE_NOTES[table.name])}")
        dbml.append("}\n")
    dbml.extend(references)
    for name, members in TABLE_GROUPS.items():
        dbml.append(f"\nTableGroup {name} {{")
        dbml.extend(f"  {member}" for member in members)
        dbml.append("}")
    return "\n".join(dbml) + "\n"


def export_schema(dbml_only=False):
    if dbml_only:
        (BACKEND_ROOT / "sql/soilsync.dbml").write_text(
            render_dbml(), encoding="utf-8", newline="\n"
        )
        print(
            f"Exported DBML for {len(Base.metadata.tables)} application tables. SQL migrations unchanged."
        )
        return
    pg = dialect()
    tables = Base.metadata.sorted_tables
    sql = [
        "-- SoilSync test schema v1. Run in soilsync_remake_test, after 000_create_database.sql.\n-- Generated by scripts/export_schema.py. Password columns hold Argon2 hashes.\n"
    ]
    for table in tables:
        sql.append(str(CreateTable(table).compile(dialect=pg)).strip() + ";\n")
        sql.extend(
            str(CreateIndex(index).compile(dialect=pg)) + ";"
            for index in sorted(table.indexes, key=lambda item: item.name)
        )
    (BACKEND_ROOT / "sql/001_schema.sql").write_text(
        "\n".join(line.rstrip() for line in "\n".join(sql).splitlines()).rstrip() + "\n",
        encoding="utf-8",
    )
    (BACKEND_ROOT / "sql/soilsync.dbml").write_text(render_dbml(), encoding="utf-8", newline="\n")
    print(f"Exported PostgreSQL SQL and DBML for {len(tables)} application tables.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dbml-only",
        action="store_true",
        help="Update the diagram without rewriting SQL migrations.",
    )
    export_schema(dbml_only=parser.parse_args().dbml_only)
