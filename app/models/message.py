from datetime import datetime
from enum import Enum

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.document_artifact import DocumentArtifact

from .base import Base


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class MessageType(str, Enum):
    TEXT = "text"
    QUIZ = "quiz"
    FLASHCARDS = "flashcards"

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column( ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True, )
    message_type: Mapped[MessageType] = mapped_column( SqlEnum( MessageType, values_callable=lambda enum: [item.value for item in enum], name="message_type"), nullable=False, default=MessageType.TEXT, server_default=MessageType.TEXT.value, )
    artifact_id: Mapped[int | None] = mapped_column( ForeignKey( "document_artifacts.id", ondelete="SET NULL", ), nullable=True, index=True, )
    artifact: Mapped["DocumentArtifact | None"] = relationship( foreign_keys=[artifact_id], )
    role: Mapped[MessageRole] = mapped_column(SqlEnum(MessageRole, values_callable=lambda enum: [e.value for e in enum], name="message_role"), nullable=False)
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)