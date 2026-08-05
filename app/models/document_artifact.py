from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.conversation import Conversation

from .base import Base

if TYPE_CHECKING:
    from app.models.message import Message


class DocumentArtifactType(str, Enum):
    SUMMARY = "summary"
    TOPICS = "topics"
    QUIZ = "quiz"
    FLASHCARDS = "flashcards"

class DocumentArtifact(Base):
    __tablename__ = "document_artifacts"


    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id: Mapped[int | None] = mapped_column( ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True, )
    type: Mapped[DocumentArtifactType] = mapped_column(SqlEnum(DocumentArtifactType, values_callable=lambda enum: [item.value for item in enum]), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    source_message_id: Mapped[int | None] = mapped_column( ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True, )
    source_message: Mapped["Message | None"] = relationship( foreign_keys=[source_message_id], )
    question_attempts: Mapped[dict[str, int]] = mapped_column( JSONB, nullable=False, server_default="{}", )
    conversation: Mapped["Conversation | None"] = relationship()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)