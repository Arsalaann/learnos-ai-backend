"""add quiz artifact type

Revision ID: 52f1ffaab8e5
Revises: 047f9129a493
Create Date: 2026-08-13 11:16:28.912063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52f1ffaab8e5'
down_revision: Union[str, Sequence[str], None] = '047f9129a493'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE documentartifacttype ADD VALUE IF NOT EXISTS 'quiz'"
    )


def downgrade() -> None:
    pass
