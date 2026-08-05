from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.embedding import get_embedding_service
from app.dependencies.llm import get_llm_service
from app.dependencies.workspace import get_current_workspace
from app.embeddings.service import EmbeddingService
from app.events.manager import workspace_event_manager
from app.llm.service import LLMService
from app.models.workspace import Workspace
from app.schemas.document_artifact import (
    DocumentArtifactResponse,
    DocumentInsightsResponse,
    InsightsGenerationResponse,
    QuizAnswerRequest,
)
from app.schemas.message import MessageResponse
from app.services.conversation_service import get_document_conversation
from app.services.document_ai_service import (
    find_document_summary,
    generate_quiz,
    get_conversation_summaries,
    get_document_insights,
    save_quiz_answer,
)
from app.services.document_artifact_service import (
    delete_conversation_summary,
    find_document_topics,
    get_document_quizzes,
)
from app.services.document_insights_background import (
    generate_document_insights_background,
)
from app.services.document_service import get_document
from app.services.documents.summarization.summarizer import (
    generate_conversation_summary,
)

router = APIRouter()









# document summary and topics

@router.get(
    "/{workspace_id}/documents/{document_id}/insights",
    response_model=DocumentInsightsResponse,
)
def get_document_insights_endpoint(
    document_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    summary, topics = get_document_insights(
        db=db,
        workspace=workspace,
        document_id=document_id,
    )

    return DocumentInsightsResponse(
        summary=summary,
        topics=topics,
    )






@router.post(
    "/{workspace_id}/documents/{document_id}/insights",
    response_model=InsightsGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_document_insights_endpoint(
    document_id: int,
    background_tasks: BackgroundTasks,
    workspace: Workspace = Depends(get_current_workspace),
    llm_service: LLMService = Depends(get_llm_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    db: Session = Depends(get_db),
):
    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
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
        return InsightsGenerationResponse(
            status="ready",
        )

    started = await workspace_event_manager.start_insights_generation(
        workspace_id=workspace.id,
        document_id=document.id,
    )

    if not started:
        return InsightsGenerationResponse(
            status="generating",
        )

    background_tasks.add_task(
        generate_document_insights_background,
        document.id,
        workspace.id,
        llm_service,
        embedding_service,
    )

    return InsightsGenerationResponse(
        status="generating",
    )
    



# conversation summaries

@router.get(
    "/{workspace_id}/documents/{document_id}/conversation-summaries",
    response_model=list[DocumentArtifactResponse],
)
def get_document_conversation_summaries_endpoint(
    document_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    conversation = get_document_conversation(
        db=db,
        workspace=workspace,
        document=document,
    )

    return get_conversation_summaries(
        db=db,
        document=document,
        conversation=conversation,
    )


@router.post(
    "/{workspace_id}/documents/{document_id}/conversation-summary",
    response_model=DocumentArtifactResponse,
)
async def generate_document_conversation_summary_endpoint(
    document_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    llm_service: LLMService = Depends(get_llm_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    db: Session = Depends(get_db),
):
    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    conversation = get_document_conversation(
        db=db,
        workspace=workspace,
        document=document,
    )

    return await generate_conversation_summary(
        db=db,
        document=document,
        conversation=conversation,
        llm_service=llm_service,
        embedding_service=embedding_service,
    )


@router.delete(
    "/{workspace_id}/documents/{document_id}/conversation-summary/{artifact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document_conversation_summary_endpoint(
    document_id: int,
    artifact_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    conversation = get_document_conversation(
        db=db,
        workspace=workspace,
        document=document,
    )

    delete_conversation_summary(
        db=db,
        document=document,
        conversation=conversation,
        artifact_id=artifact_id,
    )


# quiz

@router.post( "/{workspace_id}/documents/{document_id}/quiz", response_model=MessageResponse, )
async def generate_document_quiz_endpoint(
    document_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    llm_service: LLMService = Depends(get_llm_service),
    db: Session = Depends(get_db),
):
    return await generate_quiz(
        db=db,
        workspace=workspace,
        document_id=document_id,
        llm_service=llm_service,
    )


@router.patch(
    "/{workspace_id}/documents/{document_id}/quiz/{artifact_id}/questions/{question_index}",
    response_model=DocumentArtifactResponse,
)
def answer_quiz_question_endpoint(
    document_id: int,
    artifact_id: int,
    question_index: int,
    answer: QuizAnswerRequest,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    return save_quiz_answer(
        db=db,
        workspace=workspace,
        document_id=document_id,
        artifact_id=artifact_id,
        question_index=question_index,
        selected_option_index=answer.selected_option_index,
    )


@router.get(
    "/{workspace_id}/documents/{document_id}/quizzes",
    response_model=list[DocumentArtifactResponse],
)
def get_document_quizzes_endpoint(
    document_id: int,
    workspace: Workspace = Depends(get_current_workspace),
    db: Session = Depends(get_db),
):
    document = get_document(
        db=db,
        document_id=document_id,
        workspace=workspace,
    )

    return get_document_quizzes(
        db=db,
        document=document,
    )