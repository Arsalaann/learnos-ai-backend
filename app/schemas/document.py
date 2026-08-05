from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentUpdate(BaseModel):
    include_in_workspace_context: bool


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    content_type: str
    conversation_id: int | None
    file_size: int
    status: DocumentStatus
    stage: str | None
    progress: int | None
    processing_error: str | None
    include_in_workspace_context: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)