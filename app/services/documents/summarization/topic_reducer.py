from collections.abc import Awaitable, Callable

from app.embeddings.service import EmbeddingService
from app.schemas.document_artifact import (
    DocumentTopic,
    DocumentTopicsResponse,
)


async def reduce_topics(
    topics: list[DocumentTopic],
    embedding_service: EmbeddingService,
    consolidate_batch: Callable[
        [list[DocumentTopic]],
        Awaitable[DocumentTopicsResponse],
    ],
    max_input_tokens: int,
) -> DocumentTopicsResponse:

    if not topics:
        return DocumentTopicsResponse(topics=[])

    current = topics

    while True:
        batches: list[list[DocumentTopic]] = []
        current_batch: list[DocumentTopic] = []
        current_tokens = 0

        for topic in current:
            topic_name = topic.name.strip()

            if not topic_name:
                continue

            subtopics = [
                subtopic.strip()
                for subtopic in topic.subtopics
                if subtopic.strip()
            ]

            topic_input = DocumentTopic(
                name=topic_name,
                subtopics=subtopics,
            )

            topic_tokens = embedding_service.count_tokens(
                topic_name
            )

            for subtopic in subtopics:
                topic_tokens += embedding_service.count_tokens(
                    subtopic
                )

            if topic_tokens > max_input_tokens:
                raise ValueError(
                    "A topic exceeds the maximum topic consolidation input token budget."
                )

            if (
                current_batch
                and current_tokens + topic_tokens > max_input_tokens
            ):
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(topic_input)
            current_tokens += topic_tokens

        if current_batch:
            batches.append(current_batch)

        if not batches:
            return DocumentTopicsResponse(topics=[])

        if len(batches) == 1:
            return await consolidate_batch(batches[0])

        next_topics: list[DocumentTopic] = []

        for batch in batches:
            result = await consolidate_batch(batch)
            next_topics.extend(result.topics)

        current = next_topics