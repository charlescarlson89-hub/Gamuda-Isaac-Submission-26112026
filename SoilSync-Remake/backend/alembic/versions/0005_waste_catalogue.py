"""Add waste descriptions and catalogue IDs 32–53 without reusing existing IDs."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, insert

from alembic import op
from app.catalog_data import WASTE
from app.waste_catalogue_v1 import EXISTING_EXTRA_WASTE, EXTRA_WASTE, details_for, recipes_for

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
    op.add_column("waste_types", sa.Column("description", sa.Text()))
    op.add_column("waste_types", sa.Column("aliases", JSONB()))
    op.add_column("waste_types", sa.Column("ingredient_role", sa.String(20)))
    op.add_column("waste_types", sa.Column("reference_url", sa.Text()))
    waste = sa.table(
        "waste_types",
        sa.column("id", sa.Integer()), sa.column("name", sa.String()),
        sa.column("category", sa.String()), sa.column("is_supported", sa.Boolean()),
        sa.column("rejection_reason", sa.String()), sa.column("guide_recommendation", sa.Text()),
        sa.column("description", sa.Text()), sa.column("aliases", JSONB()),
        sa.column("ingredient_role", sa.String()), sa.column("reference_url", sa.Text()),
    )
    matches = sa.table(
        "waste_fertilizer_matches",
        sa.column("waste_type_id", sa.Integer()), sa.column("fertilizer_type_id", sa.Integer()),
    )
    def add_matches(index):
        recipe_ids = recipes_for(index)
        if recipe_ids:
            conn.execute(insert(matches).values([
                {"waste_type_id": index, "fertilizer_type_id": recipe_id}
                for recipe_id in recipe_ids
            ]).on_conflict_do_nothing(index_elements=["waste_type_id", "fertilizer_type_id"]))

    existing_rows = list(enumerate(WASTE, 1)) + list(EXISTING_EXTRA_WASTE.items())
    for index, (name, _, supported) in existing_rows:
        existing = conn.execute(waste.update().where(
            waste.c.id == index, waste.c.name == name, waste.c.is_supported == supported
        ).values(**details_for(index)).returning(waste.c.id)).scalar_one_or_none()
        if existing is not None and index in EXISTING_EXTRA_WASTE:
            add_matches(index)
    for index, (name, category, supported) in EXTRA_WASTE.items():
        details = details_for(index)
        # Unique constraints stop the migration if an ID or name was already assigned.
        conn.execute(waste.insert().values(
            id=index, name=name, category=category, is_supported=supported,
            rejection_reason=None if supported else category,
            guide_recommendation=details["description"], **details,
        ))
        add_matches(index)
    # RESTART is transactional; keep the next automatic ID ahead of existing rows.
    conn.execute(sa.text("""
        DO $$
        DECLARE
            seq regclass := pg_get_serial_sequence('waste_types', 'id');
            next_id bigint;
        BEGIN
            EXECUTE format('SELECT last_value + is_called::int FROM %s', seq) INTO next_id;
            SELECT greatest(next_id, coalesce(max(id), 0) + 1) INTO next_id FROM waste_types;
            EXECUTE format('ALTER SEQUENCE %s RESTART WITH %s', seq, next_id);
        END
        $$;
    """))


def downgrade():
    raise RuntimeError("Waste IDs may be referenced by scans; destructive downgrade is disabled.")
