"""added topics in artifacts

Revision ID: 65aa36b29d9e
Revises: 9915990cf7c7
Create Date: 2026-08-22 16:35:51.165193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65aa36b29d9e'
down_revision: Union[str, Sequence[str], None] = '9915990cf7c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE documentartifacttype ADD VALUE IF NOT EXISTS 'topics'"
    )


def downgrade() -> None:
    pass