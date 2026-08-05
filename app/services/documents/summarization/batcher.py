from app.embeddings.service import EmbeddingService
from app.models.document_chunk import DocumentChunk
from app.models.message import Message


def _get_message_text(message: Message) -> str:
    if not message.content:
        return ""

    text = message.content.get("text")

    if not isinstance(text, str):
        return ""

    return text.strip()


def build_conversation_message_batches(
    messages: list[Message],
    embedding_service: EmbeddingService,
    max_input_tokens: int,
) -> list[list[Message]]:
    batches: list[list[Message]] = []
    current_batch: list[Message] = []
    current_tokens = 0

    for message in messages:
        message_text = _get_message_text(message)

        if not message_text:
            continue

        formatted_message = f"{message.role.value}: {message_text}"

        message_tokens = embedding_service.count_tokens(
            formatted_message
        )

        if message_tokens > max_input_tokens:
            raise ValueError(
                f"Conversation message {message.id} exceeds the conversation summary input token budget."
            )

        if (
            current_batch
            and current_tokens + message_tokens > max_input_tokens
        ):
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append(message)
        current_tokens += message_tokens

    if current_batch:
        batches.append(current_batch)

    return batches


def build_summary_batches(
    chunks: list[DocumentChunk],
    embedding_service: EmbeddingService,
    max_input_tokens: int,
) -> list[list[DocumentChunk]]:
    batches: list[list[DocumentChunk]] = []
    current_batch: list[DocumentChunk] = []
    current_tokens = 0

    for chunk in chunks:
        content = chunk.content.strip()

        if not content:
            continue

        chunk_tokens = embedding_service.count_tokens(content)

        if chunk_tokens > max_input_tokens:
            raise ValueError(
                f"Document chunk {chunk.id} exceeds the summary input token budget."
            )

        if current_batch and current_tokens + chunk_tokens > max_input_tokens:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append(chunk)
        current_tokens += chunk_tokens

    if current_batch:
        batches.append(current_batch)

    return batches