"""Match small fish pin bones to sealed methods and exclude spines."""

import sqlalchemy as sa

from alembic import op
from app.models import WasteFertilizerMatch, WasteType
from app.waste_catalogue_v2 import waste_values
from app.waste_catalogue_v4 import BONE_DETAILS, FISH_PIN_BONE, FISH_PIN_BONE_ID

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
    waste = WasteType.__table__
    conn.execute(waste.insert().values(**waste_values(FISH_PIN_BONE)))
    for waste_id, (aliases, guidance) in BONE_DETAILS.items():
        conn.execute(waste.update().where(waste.c.id == waste_id).values(
            aliases=aliases, description=guidance, guide_recommendation=guidance,
        ))
    conn.execute(WasteFertilizerMatch.__table__.insert(), [
        {"waste_type_id": FISH_PIN_BONE_ID, "fertilizer_type_id": recipe_id}
        for recipe_id in FISH_PIN_BONE[-1]
    ])
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
