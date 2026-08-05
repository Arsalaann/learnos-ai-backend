from collections.abc import AsyncIterator

from sqlalchemy.orm import Session

from app.embeddings.service import EmbeddingService
from app.llm.builders.chat import build_chat_request
from app.llm.prompts import NO_CONTEXT_MESSAGE
from app.llm.schemas import LLMStreamChunk
from app.llm.service import LLMService
from app.models import Conversation
from app.services.context_service import build_context
from app.services.message_repository import get_messages


async def generate_chat_response_stream(
    db: Session,
    conversation: Conversation,
    llm_service: LLMService,
    embedding_service: EmbeddingService,
    user_message: str,
) -> AsyncIterator[LLMStreamChunk]:

    context = build_context(
        db=db,
        conversation=conversation,
        query=user_message,
        embedding_service=embedding_service,
    )

    if not context.has_context:
        yield LLMStreamChunk(content=NO_CONTEXT_MESSAGE)
        return

    request = build_chat_request(
        context=context.content,
        conversation=get_messages(
            db=db,
            conversation=conversation,
        ),
        stream=True,
    )

    async for chunk in llm_service.generate_stream(request):
        yield chunk


async def generate_chat_response(
    db: Session,
    conversation: Conversation,
    llm_service: LLMService,
    embedding_service: EmbeddingService,
    user_message: str,
) -> str:

    context = build_context(
        db=db,
        conversation=conversation,
        query=user_message,
        embedding_service=embedding_service,
    )

    if not context.has_context:
        return NO_CONTEXT_MESSAGE

    request = build_chat_request(
        context=context.content,
        conversation=get_messages(
            db=db,
            conversation=conversation,
        ),
    )

    response = await llm_service.generate(request)

    return response.content