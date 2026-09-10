"""Add soft deletion for tasks.

Revision ID: 8b72c6d901af
Revises: 5ac38a2052d1
"""

from alembic import op
import sqlalchemy as sa

revision = "8b72c6d901af"
down_revision = "5ac38a2052d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("tasks", "is_deleted")
