"""Initial supplied SoilSync user-based schema with API integrity constraints."""
from alembic import op

from app.config import BACKEND_ROOT

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().exec_driver_sql((BACKEND_ROOT / "sql/001_schema.sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Automatic destructive downgrade is disabled. Use a reviewed database backup/migration.")
