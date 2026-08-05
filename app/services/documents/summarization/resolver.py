from sqlalchemy.orm import Session

from app.models import Conversation, Document, DocumentArtifact
from app.services.document_artifact_service import (
    find_document_summary,
    find_latest_conversation_summary,
)


def get_latest_summary(
    db: Session,
    document: Document,
    conversation: Conversation,
) -> DocumentArtifact | None:

    conversation_summary = find_latest_conversation_summary(
        db=db,
        document=document,
        conversation=conversation,
    )

    if conversation_summary is not None:
        return conversation_summary

    return find_document_summary(
        db=db,
        document=document,
    )