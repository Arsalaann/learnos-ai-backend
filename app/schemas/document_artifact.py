from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentTopic(BaseModel):
    name: str = Field(min_length=1)
    subtopics: list[str] = Field(default_factory=list)

    
class SummaryBatchResponse(BaseModel):
    summary: str = Field(min_length=1)
    topics: list[DocumentTopic] = Field(default_factory=list)


class DocumentTopicsResponse(BaseModel):
    topics: list[DocumentTopic] = Field(default_factory=list)
    
    



class DocumentArtifactResponse(BaseModel):
    id: int
    document_id: int
    type: str
    content: str
    provider: str
    model: str
    question_attempts: dict[str, int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
    
class DocumentInsightsResponse(BaseModel):
    summary: DocumentArtifactResponse
    topics: DocumentArtifactResponse
    
    
    
class InsightsGenerationResponse(BaseModel):
    status: Literal["generating", "ready"]
    
    

class QuizQuestion(BaseModel):
    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=2)
    correct_option_index: int = Field(ge=0)
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_correct_option_index(self):
        if self.correct_option_index >= len(self.options):
            raise ValueError("correct_option_index must reference an existing option.")

        return self


class QuizResponse(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=1)
    
    
class QuizAnswerRequest(BaseModel):
    selected_option_index: int = Field(ge=0)
