import logging

from app.core.database import SessionLocal
from app.embeddings.service import EmbeddingService
from app.events.insights import publish_insights_status
from app.events.manager import workspace_event_manager
from app.llm.service import LLMService
from app.services.document_ai_service import generate_document_insights

logger = logging.getLogger(__name__)


async def generate_document_insights_background(
    document_id: int,
    workspace_id: int,
    llm_service: LLMService,
    embedding_service: EmbeddingService,
) -> None:
    db = SessionLocal()

    try:
        await publish_insights_status(
            workspace_id=workspace_id,
            document_id=document_id,
            status="generating",
        )

        await generate_document_insights(
            db=db,
            workspace_id=workspace_id,
            document_id=document_id,
            llm_service=llm_service,
            embedding_service=embedding_service,
        )

        await publish_insights_status(
            workspace_id=workspace_id,
            document_id=document_id,
            status="ready",
        )

        logger.info(
            "Document insights generation completed | document_id=%s",
            document_id,
        )

    except Exception:
        db.rollback()

        logger.exception(
            "Document insights generation failed | document_id=%s",
            document_id,
        )

        await publish_insights_status(
            workspace_id=workspace_id,
            document_id=document_id,
            status="failed",
            error="Document insights generation failed.",
        )

    finally:
        await workspace_event_manager.finish_insights_generation(
            workspace_id=workspace_id,
            document_id=document_id,
        )

        db.close()