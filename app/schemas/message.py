from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.message import MessageRole, MessageType
from app.schemas.document_artifact import DocumentArtifactResponse


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: MessageRole
    message_type: MessageType
    content: dict | None
    artifact_id: int | None
    artifact: DocumentArtifactResponse | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)