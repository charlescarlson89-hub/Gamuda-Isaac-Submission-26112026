"""Add Hot, Cold and Bokashi guides without reassigning existing recipe IDs."""

from pathlib import Path

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    sql = (Path(__file__).resolve().parents[1] / "data/0004_compost_methods.sql").read_text(
        encoding="utf-8"
    )
    op.get_bind().exec_driver_sql(sql)


def downgrade():
    raise RuntimeError("Recipes may be referenced by batches; destructive downgrade is disabled.")
