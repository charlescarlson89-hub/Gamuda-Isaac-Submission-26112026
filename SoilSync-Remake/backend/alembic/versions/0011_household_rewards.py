"""Add the Vinda and PETPET household reward concepts."""

import sqlalchemy as sa

from alembic import op
from app.household_rewards import household_reward_rows
from app.models import Reward

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
    conn.execute(Reward.__table__.insert(), household_reward_rows())
    conn.execute(sa.text("""
        DO $$
        DECLARE
            seq regclass := pg_get_serial_sequence('rewards', 'id');
            next_id bigint;
        BEGIN
            EXECUTE format('SELECT last_value + is_called::int FROM %s', seq) INTO next_id;
            SELECT greatest(next_id, coalesce(max(id), 0) + 1) INTO next_id FROM rewards;
            EXECUTE format('ALTER SEQUENCE %s RESTART WITH %s', seq, next_id);
        END
        $$;
    """))


def downgrade():
    raise RuntimeError("Rewards may be referenced by claims; destructive downgrade is disabled.")
