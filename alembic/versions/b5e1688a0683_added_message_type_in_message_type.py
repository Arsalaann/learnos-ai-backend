"""added message type in message type

Revision ID: b5e1688a0683
Revises: 8ee04308796f
Create Date: 2026-08-12 04:30:06.157380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5e1688a0683'
down_revision: Union[str, Sequence[str], None] = '8ee04308796f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    message_type_enum = sa.Enum(
        "text",
        "quiz",
        "flashcards",
        name="message_type",
    )

    message_type_enum.create(op.get_bind())

    op.add_column(
        "messages",
        sa.Column(
            "message_type",
            message_type_enum,
            server_default="text",
            nullable=False,
        ),
    )

    op.add_column(
        "messages",
        sa.Column(
            "artifact_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_messages_artifact_id"),
        "messages",
        ["artifact_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_messages_artifact_id_document_artifacts",
        "messages",
        "document_artifacts",
        ["artifact_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_messages_artifact_id_document_artifacts",
        "messages",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_messages_artifact_id"),
        table_name="messages",
    )

    op.drop_column("messages", "artifact_id")
    op.drop_column("messages", "message_type")

    sa.Enum(
        "text",
        "quiz",
        "flashcards",
        name="message_type",
    ).drop(op.get_bind())
