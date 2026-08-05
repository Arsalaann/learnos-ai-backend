from pydantic import BaseModel


class ContextResult(BaseModel):
    has_context: bool
    content: str
    source_count: int = 0