from fastapi import Request

from app.embeddings.service import EmbeddingService


def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service