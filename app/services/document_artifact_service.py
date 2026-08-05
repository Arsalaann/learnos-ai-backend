from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.document import Document
from app.models.document_artifact import DocumentArtifact, DocumentArtifactType


def find_artifact(
    db: Session,
    document_id: int,
    artifact_type: DocumentArtifactType,
    conversation: Conversation | None = None,
) -> DocumentArtifact | None:
    statement = (
        select(DocumentArtifact)
        .where(
            DocumentArtifact.document_id == document_id,
            DocumentArtifact.type == artifact_type,
        )
    )

    if conversation is None:
        statement = statement.where(
            DocumentArtifact.conversation_id.is_(None)
        )
    else:
        statement = statement.where(
            DocumentArtifact.conversation_id == conversation.id
        )

    result = db.execute(statement)

    return result.scalar_one_or_none()






def get_artifact(
    db: Session,
    document_id: int,
    artifact_type: DocumentArtifactType,
    conversation: Conversation | None = None,
) -> DocumentArtifact:
    artifact = find_artifact(
        db=db,
        document_id=document_id,
        artifact_type=artifact_type,
        conversation=conversation,
    )

    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found.",
        )

    return artifact




def get_document_quizzes(
    db: Session,
    document: Document,
) -> list[DocumentArtifact]:
    statement = (
        select(DocumentArtifact)
        .where(
            DocumentArtifact.document_id == document.id,
            DocumentArtifact.type == DocumentArtifactType.QUIZ,
        )
        .order_by(DocumentArtifact.created_at.desc())
    )

    result = db.execute(statement)

    return result.scalars().all()




def upsert_artifact(
    db: Session,
    document: Document,
    artifact_type: DocumentArtifactType,
    content: str,
    provider: str,
    model: str,
    conversation: Conversation | None = None,
    source_message_id: int | None = None,
) -> DocumentArtifact:

    if conversation is None:
        artifact = find_artifact(
            db=db,
            document_id=document.id,
            artifact_type=artifact_type,
        )

        if artifact:
            artifact.content = content
            artifact.provider = provider
            artifact.model = model
            return artifact

    artifact = DocumentArtifact(
        document_id=document.id,
        conversation_id=conversation.id if conversation else None,
        source_message_id=source_message_id,
        type=artifact_type,
        content=content,
        provider=provider,
        model=model,
    )

    db.add(artifact)
    db.flush()

    return artifact



def find_document_summary(
    db: Session,
    document: Document,
) -> DocumentArtifact | None:
    return find_artifact(
        db=db,
        document_id=document.id,
        artifact_type=DocumentArtifactType.SUMMARY,
    )


def find_document_topics(
    db: Session,
    document: Document,
) -> DocumentArtifact | None:

    return find_artifact(
        db=db,
        document_id=document.id,
        artifact_type=DocumentArtifactType.TOPICS,
    )


def find_latest_conversation_summary(
    db: Session,
    document: Document,
    conversation: Conversation,
) -> DocumentArtifact | None:

    statement = (
        select(DocumentArtifact)
        .where(
            DocumentArtifact.document_id == document.id,
            DocumentArtifact.conversation_id == conversation.id,
            DocumentArtifact.type == DocumentArtifactType.SUMMARY,
        )
        .order_by(DocumentArtifact.created_at.desc())
        .limit(1)
    )

    result = db.execute(statement)

    return result.scalar_one_or_none()


def find_latest_conversation_quiz(
    db: Session,
    document: Document,
    conversation: Conversation,
) -> DocumentArtifact | None:

    statement = (
        select(DocumentArtifact)
        .where(
            DocumentArtifact.document_id == document.id,
            DocumentArtifact.conversation_id == conversation.id,
            DocumentArtifact.type == DocumentArtifactType.QUIZ,
        )
        .order_by(DocumentArtifact.created_at.desc())
        .limit(1)
    )

    result = db.execute(statement)

    return result.scalar_one_or_none()


def delete_conversation_summary(
    db: Session,
    document: Document,
    conversation: Conversation,
    artifact_id: int,
) -> None:

    statement = (
        select(DocumentArtifact)
        .where(
            DocumentArtifact.id == artifact_id,
            DocumentArtifact.document_id == document.id,
            DocumentArtifact.conversation_id == conversation.id,
            DocumentArtifact.type == DocumentArtifactType.SUMMARY,
        )
    )

    result = db.execute(statement)
    artifact = result.scalar_one_or_none()

    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation summary not found.",
        )

    db.delete(artifact)
    db.commit()