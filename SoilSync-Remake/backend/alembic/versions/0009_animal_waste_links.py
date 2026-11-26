"""Add distinct small animal scraps and link them to sealed fermentation methods."""

import sqlalchemy as sa

from alembic import op
from app.models import FertilizerRecipeStep, WasteFertilizerMatch, WasteType
from app.waste_catalogue_v2 import waste_values
from app.waste_catalogue_v3 import (
    ANIMAL_LINKS,
    ANIMAL_WASTE,
    BOKASHI_SOURCE,
    BOKASHI_STEP,
    UNSPECIFIED_GUIDE,
)

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
    waste = WasteType.__table__
    links = WasteFertilizerMatch.__table__
    steps = FertilizerRecipeStep.__table__
    conn.execute(waste.insert(), [waste_values(row) | {"reference_url": BOKASHI_SOURCE} for row in ANIMAL_WASTE])
    conn.execute(links.insert(), [
        {"waste_type_id": waste_id, "fertilizer_type_id": recipe_id}
        for waste_id, recipe_id in ANIMAL_LINKS
    ])
    conn.execute(waste.update().where(waste.c.id == 22, waste.c.name == "Meat and fish").values(
        description=UNSPECIFIED_GUIDE, guide_recommendation=UNSPECIFIED_GUIDE,
    ))
    conn.execute(steps.update().where(
        steps.c.fertilizer_type_id == 6,
        steps.c.step_number == 2,
        steps.c.instruction.like("%SoilSync currently matches plant-based scraps%"),
    ).values(instruction=BOKASHI_STEP))
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
