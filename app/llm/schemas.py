from enum import Enum

from pydantic import BaseModel, Field, field_validator


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    role: MessageRole
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message content cannot be empty.")
        return value
    

class LLMResponseFormat(BaseModel):
    type: str
    json_schema: dict


class LLMRequest(BaseModel):
    messages: list[LLMMessage] = Field(min_length=1)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_output_tokens: int | None = Field(default=None, gt=0)
    stream: bool = False
    response_format: LLMResponseFormat | None = None


class GenerationMetadata(BaseModel):
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    finish_reason: str


class LLMResponse(BaseModel):
    content: str
    metadata: GenerationMetadata
    
    
class LLMStreamChunk(BaseModel):
    content: str