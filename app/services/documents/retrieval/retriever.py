from sqlalchemy import select
from sqlalchemy.orm import Session

from app.embeddings.service import EmbeddingService
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_embedding import DocumentEmbedding
from app.services.documents.constants import DEFAULT_TOP_K


def retrieve_document_chunks(
    db: Session,
    document_id: int,
    query: str,
    embedding_service: EmbeddingService,
    top_k: int = DEFAULT_TOP_K,
) -> list[DocumentChunk]:

    query_text = embedding_service.prepare_query(query)

    query_vector = embedding_service.encode(
        [query_text]
    )[0]

    statement = (
        select(DocumentChunk)
        .join(
            DocumentEmbedding,
            DocumentEmbedding.document_chunk_id
            == DocumentChunk.id,
        )
        .where(
            DocumentChunk.document_id == document_id,
        )
        .order_by(
            DocumentEmbedding.embedding.cosine_distance(
                query_vector.tolist()
            )
        )
        .limit(top_k)
    )

    result = db.execute(statement)

    return result.scalars().all()


def retrieve_workspace_chunks(
    db: Session,
    workspace_id: int,
    query: str,
    embedding_service: EmbeddingService,
    top_k: int = DEFAULT_TOP_K,
) -> list[tuple[DocumentChunk, Document]]:

    query_text = embedding_service.prepare_query(query)

    query_vector = embedding_service.encode(
        [query_text]
    )[0]

    statement = (
        select(
            DocumentChunk,
            Document,
        )
        .join(
            DocumentEmbedding,
            DocumentEmbedding.document_chunk_id
            == DocumentChunk.id,
        )
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .where(
            Document.workspace_id == workspace_id,
            Document.include_in_workspace_context.is_(True),
        )
        .order_by(
            DocumentEmbedding.embedding.cosine_distance(
                query_vector.tolist()
            )
        )
        .limit(top_k)
    )

    result = db.execute(statement)

    return result.all()