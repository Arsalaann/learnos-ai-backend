from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.embeddings.service import EmbeddingService
from app.llm.builders.summary import (
    build_conversation_batch_summary_request,
    build_conversation_summary_reduction_request,
    build_conversation_summary_regeneration_request,
    build_document_summary_reduction_request,
    build_document_summary_request,
    build_topic_consolidation_request,
)
from app.llm.config import (
    CONVERSATION_SUMMARY_INPUT_TOKEN_BUDGET,
    CONVERSATION_SUMMARY_REDUCTION_INPUT_TOKEN_BUDGET,
    SUMMARY_INPUT_TOKEN_BUDGET,
    SUMMARY_REDUCTION_INPUT_TOKEN_BUDGET,
    TOPIC_CONSOLIDATION_INPUT_TOKEN_BUDGET,
)
from app.llm.service import LLMService
from app.llm.structured import parse_structured_response
from app.models import (
    Conversation,
    Document,
    DocumentArtifact,
)
from app.models.document_artifact import DocumentArtifactType
from app.models.document_chunk import DocumentChunk
from app.schemas.document_artifact import (
    DocumentTopic,
    DocumentTopicsResponse,
    SummaryBatchResponse,
)
from app.services.document_artifact_service import (
    find_document_summary,
    find_document_topics,
    find_latest_conversation_summary,
    upsert_artifact,
)
from app.services.documents.summarization.batcher import (
    build_conversation_message_batches,
    build_summary_batches,
)
from app.services.documents.summarization.reducer import reduce_texts
from app.services.documents.summarization.topic_reducer import reduce_topics
from app.services.message_repository import (
    get_messages,
    get_messages_after,
)


@dataclass(slots=True)
class GeneratedSummary:
    content: str
    provider: str
    model: str
    topics: DocumentTopicsResponse
    
@dataclass(slots=True)
class GeneratedConversationSummary:
    content: str
    provider: str
    model: str


async def consolidate_topics(
    topics: list[DocumentTopic],
    llm_service: LLMService,
    embedding_service: EmbeddingService,
) -> DocumentTopicsResponse:

    if not topics:
        return DocumentTopicsResponse(topics=[])

    async def consolidate_batch(
        batch_topics: list[DocumentTopic],
    ) -> DocumentTopicsResponse:

        request = build_topic_consolidation_request(
            topics=batch_topics,
        )

        response = await llm_service.generate(request)

        return parse_structured_response(
            content=response.content,
            schema=DocumentTopicsResponse,
        )

    return await reduce_topics(
        topics=topics,
        embedding_service=embedding_service,
        consolidate_batch=consolidate_batch,
        max_input_tokens=TOPIC_CONSOLIDATION_INPUT_TOKEN_BUDGET,
    )


async def generate_document_summary(
    chunks: list[DocumentChunk],
    llm_service: LLMService,
    embedding_service: EmbeddingService,
) -> GeneratedSummary:

    ordered_chunks = sorted(
        chunks,
        key=lambda chunk: chunk.chunk_index,
    )

    batches = build_summary_batches(
        chunks=ordered_chunks,
        embedding_service=embedding_service,
        max_input_tokens=SUMMARY_INPUT_TOKEN_BUDGET,
    )

    if not batches:
        raise ValueError(
            "Cannot generate a summary from an empty document."
        )

    summaries: list[str] = []
    batch_topics: list[DocumentTopic] = []

    provider: str | None = None
    model: str | None = None

    async def summarize_document_batch(
        content: str,
    ) -> SummaryBatchResponse:

        nonlocal provider, model

        request = build_document_summary_request(
            content=content,
        )

        response = await llm_service.generate(request)

        provider = response.metadata.provider
        model = response.metadata.model

        result = parse_structured_response(
            content=response.content,
            schema=SummaryBatchResponse,
        )

        if not result.summary.strip():
            raise ValueError(
                "LLM returned an empty document summary."
            )

        return result

    for batch in batches:
        content = "\n\n".join(
            chunk.content
            for chunk in batch
        )

        result = await summarize_document_batch(content)

        summaries.append(result.summary)
        batch_topics.extend(result.topics)


    topics = await consolidate_topics(
        topics=batch_topics,
        llm_service=llm_service,
        embedding_service=embedding_service,
    )

    async def reduce_summary_batch(
        content: str,
    ) -> str:

        nonlocal provider, model

        request = build_document_summary_reduction_request(
            summaries=content,
        )

        response = await llm_service.generate(request)

        provider = response.metadata.provider
        model = response.metadata.model

        if not response.content.strip():
            raise ValueError(
                "LLM returned an empty reduced summary."
            )

        return response.content

    final_summary = await reduce_texts(
        texts=summaries,
        embedding_service=embedding_service,
        summarize_batch=reduce_summary_batch,
        max_input_tokens=SUMMARY_REDUCTION_INPUT_TOKEN_BUDGET,
    )

    if provider is None or model is None:
        raise ValueError(
            "Summary generation did not produce LLM metadata."
        )

    return GeneratedSummary(
        content=final_summary,
        provider=provider,
        model=model,
        topics=topics,
    )


def save_document_summary_artifacts(
    db: Session,
    document: Document,
    generated: GeneratedSummary,
) -> tuple[DocumentArtifact, DocumentArtifact]:

    summary_artifact = upsert_artifact(
        db=db,
        document=document,
        artifact_type=DocumentArtifactType.SUMMARY,
        content=generated.content,
        provider=generated.provider,
        model=generated.model,
    )

    topics_artifact = upsert_artifact(
        db=db,
        document=document,
        artifact_type=DocumentArtifactType.TOPICS,
        content=generated.topics.model_dump_json(),
        provider=generated.provider,
        model=generated.model,
    )

    db.commit()

    db.refresh(summary_artifact)
    db.refresh(topics_artifact)

    return summary_artifact, topics_artifact









async def reduce_conversation_summary(
    content: str,
    llm_service: LLMService,
) -> GeneratedConversationSummary:
    request = build_conversation_summary_reduction_request(
        summaries=content,
    )

    response = await llm_service.generate(request)

    if not response.content.strip():
        raise ValueError(
            "LLM returned an empty reduced conversation summary."
        )

    return GeneratedConversationSummary(
        content=response.content,
        provider=response.metadata.provider,
        model=response.metadata.model,
    )






async def generate_conversation_summary(
    db: Session,
    document: Document,
    conversation: Conversation,
    llm_service: LLMService,
    embedding_service: EmbeddingService,
) -> DocumentArtifact:

    document_summary_artifact = find_document_summary(
        db=db,
        document=document,
    )

    document_topics_artifact = find_document_topics(
        db=db,
        document=document,
    )

    if document_summary_artifact is None or document_topics_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document insights must be generated before generating a conversation summary.",
        )

    latest_conversation_summary = find_latest_conversation_summary(
        db=db,
        document=document,
        conversation=conversation,
    )

    if (
        latest_conversation_summary is None
        or latest_conversation_summary.source_message_id is None
    ):
        messages = get_messages(
            db=db,
            conversation=conversation,
        )
    else:
        messages = get_messages_after(
            db=db,
            conversation=conversation,
            message_id=latest_conversation_summary.source_message_id,
        )

    # No previous summary + no messages = nothing to summarize.
    if not messages and latest_conversation_summary is None:
        raise ValueError(
            "Cannot generate a conversation summary without message content."
        )

    # ---------------------------------------------------------
    # Case 1: New messages exist.
    # Summarize ONLY those new messages.
    # ---------------------------------------------------------

    if messages:
        batches = build_conversation_message_batches(
            messages=messages,
            embedding_service=embedding_service,
            max_input_tokens=CONVERSATION_SUMMARY_INPUT_TOKEN_BUDGET,
        )

        if not batches:
            raise ValueError(
                "Cannot generate a conversation summary without message content."
            )

        batch_summaries: list[str] = []
        provider: str | None = None
        model: str | None = None

        for batch in batches:
            messages_text = "\n\n".join(
                f"{message.role.value}: {message.content['text'].strip()}"
                for message in batch
                if (
                    message.content
                    and isinstance(message.content.get("text"), str)
                    and message.content["text"].strip()
                )
            )

            if not messages_text:
                continue

            request = build_conversation_batch_summary_request(
                messages=messages_text,
            )

            response = await llm_service.generate(request)

            if not response.content.strip():
                raise ValueError(
                    "LLM returned an empty conversation batch summary."
                )

            batch_summaries.append(response.content)

            provider = response.metadata.provider
            model = response.metadata.model

        if not batch_summaries:
            raise ValueError(
                "Cannot generate a conversation summary without message content."
            )

        if len(batch_summaries) == 1:
            final_summary = batch_summaries[0]

        else:
            reduced = await reduce_texts(
                texts=batch_summaries,
                embedding_service=embedding_service,
                summarize_batch=lambda content: reduce_conversation_summary(
                    content=content,
                    llm_service=llm_service,
                ),
                max_input_tokens=CONVERSATION_SUMMARY_REDUCTION_INPUT_TOKEN_BUDGET,
            )

            # reduce_texts currently returns only the final text, so the
            # provider/model from the batch call remains the metadata source.
            final_summary = reduced

        if provider is None or model is None:
            raise ValueError(
                "Conversation summary generation did not produce LLM metadata."
            )

        latest_message = messages[-1]

        artifact = DocumentArtifact(
            document_id=document.id,
            conversation_id=conversation.id,
            type=DocumentArtifactType.SUMMARY,
            content=final_summary,
            provider=provider,
            model=model,
            source_message_id=latest_message.id,
        )

        db.add(artifact)
        db.commit()
        db.refresh(artifact)

        return artifact

    # ---------------------------------------------------------
    # Case 2: No new messages.
    # Regenerate the existing summary and update the same
    # artifact instead of creating another one.
    # ---------------------------------------------------------

    request = build_conversation_summary_regeneration_request(
        summary=latest_conversation_summary.content,
    )

    response = await llm_service.generate(request)

    if not response.content.strip():
        raise ValueError(
            "LLM returned an empty regenerated conversation summary."
        )

    latest_conversation_summary.content = response.content
    latest_conversation_summary.provider = response.metadata.provider
    latest_conversation_summary.model = response.metadata.model

    db.commit()
    db.refresh(latest_conversation_summary)

    return latest_conversation_summary