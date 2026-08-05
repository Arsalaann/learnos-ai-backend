from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ConversationType


class ConversationCreate(BaseModel):
    title: str | None = None
    
    
    
class ConversationUpdate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )


class ConversationResponse(BaseModel):
    id: int
    document_id: int | None
    conversation_type: ConversationType
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)