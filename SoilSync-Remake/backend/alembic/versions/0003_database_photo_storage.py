"""Optional private proof storage for the hosted PostgreSQL deployment."""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE weekly_checkin_quests ADD COLUMN photo_data BYTEA")


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; use a reviewed backup/migration.")
