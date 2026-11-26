"""Add waste types and link Neon catalogue entries to Atlas method IDs."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from alembic import op
from app.models import WasteFertilizerMatch, WasteType
from app.waste_catalogue_v2 import NEW_WASTE, WASTE_LINKS, waste_values

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
    waste = WasteType.__table__
    links = WasteFertilizerMatch.__table__
    conn.execute(waste.insert(), [waste_values(row) for row in NEW_WASTE])
    supported = dict(conn.execute(
        sa.select(waste.c.name, waste.c.id).where(waste.c.is_supported)
    ).all())
    conn.execute(insert(links).values([
        {"waste_type_id": supported[name], "fertilizer_type_id": recipe_id}
        for name, recipe_id in WASTE_LINKS if name in supported
    ]).on_conflict_do_nothing(index_elements=["waste_type_id", "fertilizer_type_id"]))
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
