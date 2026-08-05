import asyncio
import logging

from app.core.database import SessionLocal
from app.embeddings.service import EmbeddingService
from app.events.document_events import publish_document_status
from app.models.document import Document, DocumentStatus
from app.services.documents.processing_service import process_document

logger = logging.getLogger(__name__)


def _process_document_sync(
    document_id: int,
    embedding_service: EmbeddingService,
    loop: asyncio.AbstractEventLoop,
) -> tuple[int, int, str | None]:

    db = SessionLocal()

    try:
        document = db.get(Document, document_id)

        if document is None:
            logger.error(
                "Document processing failed | document_id=%s | reason=document_not_found",
                document_id,
            )
            return document_id, 0, "Document not found."

        workspace_id = document.workspace_id

        def progress_callback(
            stage: str,
            progress: int,
        ) -> None:

            document.stage = stage
            document.progress = progress

            db.commit()

            asyncio.run_coroutine_threadsafe(
                publish_document_status(
                    workspace_id=workspace_id,
                    document_id=document_id,
                    status=DocumentStatus.PROCESSING.value,
                    stage=stage,
                    progress=progress,
                ),
                loop,
            )

        process_document(
            db=db,
            document=document,
            embedding_service=embedding_service,
            progress_callback=progress_callback,
        )

        document.status = DocumentStatus.READY
        document.stage = "completed"
        document.progress = 100
        document.processing_error = None

        db.commit()

        return workspace_id, document.id, None

    except Exception:
        db.rollback()

        logger.exception(
            "Document processing failed | document_id=%s",
            document_id,
        )

        document = db.get(Document, document_id)

        if document is not None:
            document.status = DocumentStatus.FAILED
            document.processing_error = (
                "Document processing failed. You can reprocess the document."
            )

            db.commit()

            return (
                document.workspace_id,
                document.id,
                document.processing_error,
            )

        return document_id, 0, "Document processing failed."

    finally:
        db.close()


async def process_document_background(
    document_id: int,
    embedding_service: EmbeddingService,
) -> None:

    loop = asyncio.get_running_loop()

    workspace_id, processed_document_id, processing_error = (
        await asyncio.to_thread(
            _process_document_sync,
            document_id,
            embedding_service,
            loop,
        )
    )

    if processed_document_id == 0:
        return

    if processing_error:
        await publish_document_status(
            workspace_id=workspace_id,
            document_id=processed_document_id,
            status=DocumentStatus.FAILED.value,
            processing_error=processing_error,
        )

        logger.error(
            "Document processing failed | document_id=%s",
            processed_document_id,
        )

        return

    await publish_document_status(
        workspace_id=workspace_id,
        document_id=processed_document_id,
        status=DocumentStatus.READY.value,
        stage="completed",
        progress=100,
        processing_error=None,
    )

    logger.info(
        "Document processing completed | document_id=%s",
        processed_document_id,
    )