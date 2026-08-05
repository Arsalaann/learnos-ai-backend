import json

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.embeddings.service import EmbeddingService
from app.llm.builders.quiz import build_quiz_request
from app.llm.service import LLMService
from app.llm.structured import parse_structured_response
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.document_artifact import DocumentArtifact, DocumentArtifactType
from app.models.document_chunk import DocumentChunk
from app.models.message import MessageRole, MessageType
from app.models.workspace import Workspace
from app.schemas.document_artifact import QuizResponse
from app.services.conversation_service import (
    get_conversation_context,
    get_document_conversation,
)
from app.services.document_artifact_service import (
    find_document_summary,
    find_document_topics,
    get_artifact,
    upsert_artifact,
)
from app.services.document_service import get_document
from app.services.documents.summarization.summarizer import (
    generate_document_summary,
    save_document_summary_artifacts,
)
from app.services.message_repository import get_message
from app.services.message_service import create_message


def get_artifact_by_id(
    db: Session,
    document: Document,
    artifact_id: int,
) -> DocumentArtifact:
    statement = (
        select(DocumentArtifact)
        .where(
            DocumentArtifact.id == artifact_id,
            DocumentArtifact.document_id == document.id,
        )
    )

    result = db.execute(statement)

    artifact = result.scalar_one_or_none()

    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document artifact not found.",
        )

    return artifact


def get_summary(
    db: Session,
    workspace: Workspace,
    document_id: int,
) -> DocumentArtifact:
    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    return get_artifact(
        db=db,
        document_id=document.id,
        artifact_type=DocumentArtifactType.SUMMARY,
    )


def get_conversation_summaries(
    db: Session,
    document: Document,
    conversation: Conversation,
) -> list[DocumentArtifact]:
    statement = (
        select(DocumentArtifact)
        .where(
            DocumentArtifact.document_id == document.id,
            DocumentArtifact.conversation_id == conversation.id,
            DocumentArtifact.type == DocumentArtifactType.SUMMARY,
        )
        .order_by(DocumentArtifact.created_at.desc())
    )

    result = db.execute(statement)

    return result.scalars().all()




def get_document_insights(
    db: Session,
    workspace: Workspace,
    document_id: int,
) -> tuple[DocumentArtifact, DocumentArtifact]:
    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    summary = find_document_summary(
        db=db,
        document=document,
    )

    topics = find_document_topics(
        db=db,
        document=document,
    )

    if summary is None or topics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document insights not found.",
        )

    return summary, topics






async def generate_document_insights(
    db: Session,
    workspace_id: int,
    document_id: int,
    llm_service: LLMService,
    embedding_service: EmbeddingService,
) -> tuple[DocumentArtifact, DocumentArtifact]:

    document = db.get(Document, document_id)

    if document is None or document.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    existing_summary = find_document_summary(
        db=db,
        document=document,
    )

    existing_topics = find_document_topics(
        db=db,
        document=document,
    )

    if existing_summary is not None and existing_topics is not None:
        return existing_summary, existing_topics

    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.chunk_index)
    )

    result = db.execute(statement)

    chunks = result.scalars().all()

    generated = await generate_document_summary(
        chunks=chunks,
        llm_service=llm_service,
        embedding_service=embedding_service,
    )

    summary_artifact, topics_artifact = save_document_summary_artifacts(
        db=db,
        document=document,
        generated=generated,
    )

    return summary_artifact, topics_artifact







async def generate_quiz(
    db: Session,
    workspace: Workspace,
    document_id: int,
    llm_service: LLMService,
):
    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    document_summary = find_document_summary(
        db=db,
        document=document,
    )

    document_topics = find_document_topics(
        db=db,
        document=document,
    )

    if document_summary is None or document_topics is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document insights must be generated before generating a quiz.",
        )

    conversation = get_document_conversation(
        db=db,
        workspace=workspace,
        document=document,
    )

    conversation_context = get_conversation_context(
        db=db,
        document=document,
        conversation=conversation,
    )

    request = build_quiz_request(
        document_text=document_summary.content,
        conversation_summary=(
            conversation_context.summary.content
            if conversation_context.summary is not None
            else None
        ),
        conversation=conversation_context.messages,
    )

    response = await llm_service.generate(request)

    quiz = parse_structured_response(
        content=response.content,
        schema=QuizResponse,
    )

    artifact = upsert_artifact(
        db=db,
        document=document,
        artifact_type=DocumentArtifactType.QUIZ,
        content=json.dumps(quiz.model_dump()),
        provider=response.metadata.provider,
        model=response.metadata.model,
        conversation=conversation,
        source_message_id=None,
    )

    quiz_message = create_message(
        db=db,
        conversation=conversation,
        role=MessageRole.ASSISTANT,
        message_type=MessageType.QUIZ,
        content=None,
        artifact_id=artifact.id,
    )

    db.commit()

    return get_message(
        db=db,
        message_id=quiz_message.id,
    )
    
    
    

def save_quiz_answer(
    db: Session,
    workspace: Workspace,
    document_id: int,
    artifact_id: int,
    question_index: int,
    selected_option_index: int,
) -> DocumentArtifact:
    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    artifact = get_artifact_by_id(
        db=db,
        document=document,
        artifact_id=artifact_id,
    )

    if artifact.type != DocumentArtifactType.QUIZ:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Artifact is not a quiz.",
        )

    quiz = parse_structured_response(
        content=artifact.content,
        schema=QuizResponse,
    )

    if question_index < 0 or question_index >= len(quiz.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question index.",
        )

    question = quiz.questions[question_index]

    if selected_option_index < 0 or selected_option_index >= len(question.options):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid option index.",
        )

    question_key = str(question_index)

    if question_key in artifact.question_attempts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question has already been answered.",
        )

    question_attempts = dict(artifact.question_attempts)
    question_attempts[question_key] = selected_option_index
    artifact.question_attempts = question_attempts

    db.commit()
    db.refresh(artifact)

    return artifact