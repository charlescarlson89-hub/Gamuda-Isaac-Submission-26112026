"""Store encrypted personal Gemini credentials by account."""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gemini_credentials",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("encrypted_key", sa.LargeBinary(), nullable=False),
    )


def downgrade():
    raise RuntimeError("Downgrading would delete saved credentials.")
