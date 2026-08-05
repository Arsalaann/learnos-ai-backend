import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.embeddings.factory import create_embedding_service
from app.llm.factory import create_llm_http_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    http_client = None

    try:
        http_client = create_llm_http_client()

        embedding_service = create_embedding_service()

        app.state.http_client = http_client
        app.state.embedding_service = embedding_service

        logger.info("Application resources initialized.")

        yield

    except Exception:
        logger.exception(
            "Failed to initialize application resources."
        )
        raise

    finally:
        if http_client is not None:
            await http_client.aclose()

            logger.info("Application HTTP resources closed.")