"""Record separate chicken bones and clarify fish-bone acceptance."""

import sqlalchemy as sa

from alembic import op
from app.models import WasteFertilizerMatch, WasteType
from app.waste_catalogue_v2 import waste_values
from app.waste_catalogue_v4 import (
    CHICKEN_BONE,
    CHICKEN_BONE_ID,
    FISH_PIN_BONE_ID,
    REJECTED_BONE_ALIASES,
    REJECTED_BONE_GUIDANCE,
    REJECTED_BONE_ID,
    SMALL_FISH_BONE,
)

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
    waste = WasteType.__table__
    links = WasteFertilizerMatch.__table__

    fish = waste_values(SMALL_FISH_BONE)
    del fish["id"]
    conn.execute(waste.update().where(waste.c.id == FISH_PIN_BONE_ID).values(**fish))
    conn.execute(waste.update().where(waste.c.id == REJECTED_BONE_ID).values(
        aliases=REJECTED_BONE_ALIASES,
        description=REJECTED_BONE_GUIDANCE,
        guide_recommendation=REJECTED_BONE_GUIDANCE,
    ))
    conn.execute(waste.insert().values(**waste_values(CHICKEN_BONE)))
    conn.execute(links.insert(), [
        {"waste_type_id": CHICKEN_BONE_ID, "fertilizer_type_id": recipe_id}
        for recipe_id in CHICKEN_BONE[-1]
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
