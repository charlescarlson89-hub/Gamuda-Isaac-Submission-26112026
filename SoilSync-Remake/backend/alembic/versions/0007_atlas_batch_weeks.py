"""Reserve the new method IDs and allow timeline-based batch check-ins."""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("weekly_checkin_quests", sa.Column("available_on", sa.Date()))
    op.drop_constraint("weekly_checkin_quests_week_number_check", "weekly_checkin_quests", type_="check")
    op.create_check_constraint(
        "weekly_checkin_quests_week_number_check", "weekly_checkin_quests", "week_number BETWEEN 1 AND 105"
    )
    op.drop_constraint("batches_percentage_completed_check", "batches", type_="check")
    op.create_check_constraint("batches_percentage_completed_check", "batches", "percentage_completed BETWEEN 0 AND 100")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM fertilizer_types
                WHERE (id = 7 AND name <> 'Blender Slurry & Soil Factory')
                   OR (id = 8 AND name <> 'DIY Rice Water Inoculant')
            ) THEN
                RAISE EXCEPTION 'A new SoilSync method ID is already in use';
            END IF;
        END $$;
    """)
    op.execute("""
        INSERT INTO fertilizer_types (id, name, description, est_days_to_finish)
        VALUES (7, 'Blender Slurry & Soil Factory', 'A method for suitable plant-based scraps.', 21),
               (8, 'DIY Rice Water Inoculant', 'A fermentation method for selected plant-based scraps.', 28)
        ON CONFLICT (id) DO NOTHING
    """)
    op.execute("""
        SELECT setval(pg_get_serial_sequence('fertilizer_types', 'id'),
            GREATEST((SELECT max(id) FROM fertilizer_types), 8))
    """)


def downgrade():
    raise RuntimeError("Downgrading could invalidate existing batches and weekly claims.")
