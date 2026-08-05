"""add default workspace flag

Revision ID: affa92b5742d
Revises: 52f1ffaab8e5
Create Date: 2026-08-17 09:55:02.273826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'affa92b5742d'
down_revision: Union[str, Sequence[str], None] = '52f1ffaab8e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("workspaces", sa.Column("is_default", sa.Boolean(), nullable=True, server_default=sa.false()))

    op.execute(
        """
        UPDATE workspaces
        SET is_default = false
        WHERE is_default IS NULL
        """
    )

    op.execute(
        """
        UPDATE workspaces
        SET is_default = true
        WHERE id IN (
            SELECT DISTINCT ON (user_id) id
            FROM workspaces
            ORDER BY user_id, created_at ASC, id ASC
        )
        """
    )

    op.alter_column("workspaces", "is_default", nullable=False, server_default=None)

    op.create_index(
        "uq_workspace_user_default",
        "workspaces",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )
    
def downgrade() -> None:
    op.drop_index("uq_workspace_user_default", table_name="workspaces")
    op.drop_column("workspaces", "is_default")