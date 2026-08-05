from sqlalchemy import select
from sqlalchemy.orm import Session

from app.embeddings.service import EmbeddingService
from app.models import Conversation, ConversationType, Document
from app.models.document_chunk import DocumentChunk
from app.schemas.context import ContextResult
from app.services.documents.retrieval.retriever import (
    retrieve_document_chunks,
    retrieve_workspace_chunks,
)


def _load_conversation_document(
    db: Session,
    conversation: Conversation,
) -> Document:

    statement = (
        select(Document)
        .where(Document.id == conversation.document_id)
    )

    result = db.execute(statement)

    return result.scalar_one()


def build_context(
    db: Session,
    conversation: Conversation,
    query: str,
    embedding_service: EmbeddingService,
) -> ContextResult:

    if conversation.conversation_type == ConversationType.DOCUMENT:
        document = _load_conversation_document(
            db=db,
            conversation=conversation,
        )

        chunks = retrieve_document_chunks(
            db=db,
            document_id=document.id,
            query=query,
            embedding_service=embedding_service,
        )

        if not chunks:
            return ContextResult(
                has_context=False,
                content="",
            )

        content = _build_document_context(
            document=document,
            chunks=chunks,
        )

        return ContextResult(
            has_context=bool(content.strip()),
            content=content,
            source_count=len(chunks),
        )

    workspace_chunks = retrieve_workspace_chunks(
        db=db,
        workspace_id=conversation.workspace_id,
        query=query,
        embedding_service=embedding_service,
    )

    if not workspace_chunks:
        return ContextResult(
            has_context=False,
            content="",
        )

    content = _build_workspace_context(
        workspace_chunks=workspace_chunks,
    )

    return ContextResult(
        has_context=bool(content.strip()),
        content=content,
        source_count=len(workspace_chunks),
    )


def _build_document_context(
    document: Document,
    chunks: list[DocumentChunk],
) -> str:

    sections = []

    for chunk in chunks:
        sections.append(
            f"## Source {chunk.chunk_index + 1}\n\n"
            f"{chunk.content}"
        )

    return (
        f"# Document\n"
        f"Filename: {document.original_filename}\n\n"
        + "\n\n".join(sections)
    )


def _build_workspace_context(
    workspace_chunks: list[tuple[DocumentChunk, Document]],
) -> str:

    sections = []

    for chunk, document in workspace_chunks:
        sections.append(
            f"# Document\n"
            f"Filename: {document.original_filename}\n\n"
            f"## Source {chunk.chunk_index + 1}\n\n"
            f"{chunk.content}"
        )

    return "\n\n---\n\n".join(sections)