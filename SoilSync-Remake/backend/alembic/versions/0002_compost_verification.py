"""Record visual compost approval and prevent reuse of a weekly proof image."""

from alembic import op

from app.config import BACKEND_ROOT

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().exec_driver_sql(
        (BACKEND_ROOT / "sql/004_compost_verification.sql").read_text(encoding="utf-8")
    )


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled; use a reviewed backup/migration.")
