from collections.abc import Callable

from sqlalchemy.orm import Session

from app.embeddings.service import EmbeddingService
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.document_embedding import DocumentEmbedding
from app.services.documents.chunking.chunker import chunk_blocks
from app.services.documents.constants import EMBEDDING_BATCH_SIZE
from app.services.documents.extraction.extractor import extract_document


def process_document(
    db: Session,
    document: Document,
    embedding_service: EmbeddingService,
    progress_callback: Callable[[str, int], None],
) -> None:

    progress_callback("reading", 5)

    extraction_result = extract_document(
        content_type=document.content_type,
        storage_path=document.storage_path,
        upload_directory=document.upload_directory,
    )

    progress_callback("reading", 25)

    chunks = chunk_blocks(
        blocks=extraction_result.blocks,
        embedding_service=embedding_service,
    )

    progress_callback("preparing", 40)

    if not chunks:
        raise ValueError(
            "No readable content could be extracted from the document."
    )

    document_chunks: list[DocumentChunk] = []

    for chunk in chunks:
        document_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=chunk.index,
            content=chunk.content,
            source_start=chunk.source_start,
            source_end=chunk.source_end,
        )

        document_chunks.append(document_chunk)

    db.add_all(document_chunks)
    db.flush()

    total_batches = (
        len(document_chunks) + EMBEDDING_BATCH_SIZE - 1
    ) // EMBEDDING_BATCH_SIZE

    for batch_number, start in enumerate(
        range(0, len(document_chunks), EMBEDDING_BATCH_SIZE),
        start=1,
    ):
        batch_chunks = document_chunks[
            start:start + EMBEDDING_BATCH_SIZE
        ]

        texts = embedding_service.prepare_passages(
            [chunk.content for chunk in batch_chunks]
        )

        vectors = embedding_service.encode(texts)

        embeddings = [
            DocumentEmbedding(
                document_chunk_id=chunk.id,
                embedding=vector.tolist(),
                model=embedding_service.model_name,
            )
            for chunk, vector in zip(
                batch_chunks,
                vectors,
                strict=True,
            )
        ]

        db.add_all(embeddings)

        progress = 40 + int(
            (batch_number / total_batches) * 55
        )

        progress_callback("analyzing", progress)

    db.flush()

    progress_callback("finishing", 98)