from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.embeddings.service import EmbeddingService
from app.llm.schemas import LLMStreamChunk
from app.llm.service import LLMService
from app.models import Conversation, Message, MessageRole, MessageType
from app.services.ai_service import (
    generate_chat_response,
    generate_chat_response_stream,
)


async def send_message_stream(
    db: Session,
    conversation: Conversation,
    llm_service: LLMService,
    embedding_service: EmbeddingService,
    user_message: str,
) -> AsyncIterator[LLMStreamChunk]:

    create_message(
        db=db,
        conversation=conversation,
        role=MessageRole.USER,
        message_type=MessageType.TEXT,
        content=_text_content(user_message),
    )

    full_content: list[str] = []

    async for chunk in generate_chat_response_stream(
        db=db,
        conversation=conversation,
        llm_service=llm_service,
        embedding_service=embedding_service,
        user_message=user_message,
    ):
        full_content.append(chunk.content)
        yield chunk

    assistant_text = "".join(full_content)

    create_message(
        db=db,
        conversation=conversation,
        role=MessageRole.ASSISTANT,
        message_type=MessageType.TEXT,
        content=_text_content(assistant_text),
    )

    db.commit()


async def send_message(
    db: Session,
    conversation: Conversation,
    llm_service: LLMService,
    embedding_service: EmbeddingService,
    user_message: str,
):

    create_message(
        db=db,
        conversation=conversation,
        role=MessageRole.USER,
        message_type=MessageType.TEXT,
        content=_text_content(user_message),
    )

    assistant_text = await generate_chat_response(
        db=db,
        conversation=conversation,
        llm_service=llm_service,
        embedding_service=embedding_service,
        user_message=user_message,
    )

    assistant_message = create_message(
        db=db,
        conversation=conversation,
        role=MessageRole.ASSISTANT,
        message_type=MessageType.TEXT,
        content=_text_content(assistant_text),
    )

    db.commit()
    db.refresh(assistant_message)

    return assistant_message


def create_message(
    db: Session,
    conversation: Conversation,
    role: MessageRole,
    message_type: MessageType,
    content: dict | None,
    artifact_id: int | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation.id,
        role=role,
        message_type=message_type,
        content=content,
        artifact_id=artifact_id,
    )

    db.add(message)
    db.flush()

    return message


def _text_content(text: str) -> dict:
    return {
        "text": text,
    }


def get_latest_message(
    db: Session,
    conversation: Conversation,
) -> Message | None:
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(1)
    )

    result = db.execute(statement)

    return result.scalar_one_or_none()