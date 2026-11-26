"""Link small thin animal bones to the sealed rice-water Bokashi process."""

from sqlalchemy.dialects.postgresql import insert

from alembic import op
from app.models import WasteFertilizerMatch, WasteType
from app.waste_catalogue_v4 import (
    SMALL_ANIMAL_BONE_GUIDANCE,
    SMALL_ANIMAL_BONE_ID,
    SMALL_ANIMAL_BONE_RICE_WATER_LINK,
)

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
    waste = WasteType.__table__
    links = WasteFertilizerMatch.__table__
    waste_id, recipe_id = SMALL_ANIMAL_BONE_RICE_WATER_LINK
    conn.execute(waste.update().where(waste.c.id == waste_id).values(
        description=SMALL_ANIMAL_BONE_GUIDANCE, guide_recommendation=SMALL_ANIMAL_BONE_GUIDANCE,
    ))
    conn.execute(insert(links).values(waste_type_id=waste_id, fertilizer_type_id=recipe_id)
                 .on_conflict_do_nothing(index_elements=["waste_type_id", "fertilizer_type_id"]))


def downgrade():
    from app.waste_catalogue_v4 import BONE_DETAILS

    waste = WasteType.__table__
    links = WasteFertilizerMatch.__table__
    waste_id, recipe_id = SMALL_ANIMAL_BONE_RICE_WATER_LINK
    op.execute(links.delete().where(links.c.waste_type_id == waste_id, links.c.fertilizer_type_id == recipe_id))
    guidance = BONE_DETAILS[SMALL_ANIMAL_BONE_ID][1]
    op.execute(waste.update().where(waste.c.id == waste_id).values(
        description=guidance, guide_recommendation=guidance,
    ))
