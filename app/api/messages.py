import asyncio
import json

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.conversation import get_conversation
from app.dependencies.embedding import get_embedding_service
from app.dependencies.llm import get_llm_service
from app.embeddings.service import EmbeddingService
from app.llm.service import LLMService
from app.models import Conversation
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message_repository import (
    delete_message,
    get_messages,
)
from app.services.message_service import send_message, send_message_stream

router = APIRouter()


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream_endpoint(
    message: MessageCreate,
    conversation: Conversation = Depends(get_conversation),
    llm_service: LLMService = Depends(get_llm_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    db: Session = Depends(get_db),
):
    async def event_stream():
        try:
            async for chunk in send_message_stream(
                db=db,
                conversation=conversation,
                llm_service=llm_service,
                embedding_service=embedding_service,
                user_message=message.content,
            ):
                yield (
                    "event: token\n"
                    f"data: {json.dumps({'content': chunk.content})}\n\n"
                )

            yield "event: done\ndata: {}\n\n"

        except asyncio.CancelledError:
            db.rollback()
            raise

        except Exception:  # noqa: BLE001
            db.rollback()

            yield (
                "event: error\n"
                f"data: {json.dumps({'message': 'Failed to generate response.'})}\n\n"
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message_endpoint(
    message: MessageCreate,
    conversation: Conversation = Depends(get_conversation),
    llm_service: LLMService = Depends(get_llm_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    db: Session = Depends(get_db),
):
    return await send_message(
        db=db,
        conversation=conversation,
        llm_service=llm_service,
        embedding_service=embedding_service,
        user_message=message.content,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages_endpoint(
    conversation: Conversation = Depends(get_conversation),
    db: Session = Depends(get_db),
):
    return get_messages(
        db=db,
        conversation=conversation,
    )


@router.delete(
    "/{conversation_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_message_endpoint(
    message_id: int,
    conversation: Conversation = Depends(get_conversation),
    db: Session = Depends(get_db),
):
    delete_message(
        db=db,
        conversation=conversation,
        message_id=message_id,
    )