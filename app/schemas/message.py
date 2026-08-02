from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.message import MessageRole

class MessageCreate(BaseModel):
    content: dict
    document_id: int | None = None
    
class MessageResponse(BaseModel):
    id: int
    document_id: int | None
    role: MessageRole
    content: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)