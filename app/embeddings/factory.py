from app.core.config import settings
from app.embeddings.providers.sentence_transformer import (
    SentenceTransformerProvider,
)
from app.embeddings.service import EmbeddingService


def create_embedding_service() -> EmbeddingService:
    if settings.EMBEDDING_PROVIDER == "sentence_transformer":
        provider = SentenceTransformerProvider(
            model_name=settings.EMBEDDING_MODEL,
        )

        return EmbeddingService(provider=provider)

    raise ValueError(
        f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}"
    )