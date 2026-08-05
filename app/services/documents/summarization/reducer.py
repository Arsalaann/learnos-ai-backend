from collections.abc import Awaitable, Callable

from app.embeddings.service import EmbeddingService


async def reduce_texts(
    texts: list[str],
    embedding_service: EmbeddingService,
    summarize_batch: Callable[[str], Awaitable[str]],
    max_input_tokens: int,
) -> str:
    if not texts:
        raise ValueError("Cannot reduce an empty list of texts.")

    current = texts

    while len(current) > 1:
        batches: list[list[str]] = []
        current_batch: list[str] = []
        current_tokens = 0

        for text in current:
            text = text.strip()

            if not text:
                continue

            text_tokens = embedding_service.count_tokens(text)

            if text_tokens > max_input_tokens:
                raise ValueError(
                    "A summary exceeds the maximum input token budget."
                )

            if current_batch and current_tokens + text_tokens > max_input_tokens:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(text)
            current_tokens += text_tokens

        if current_batch:
            batches.append(current_batch)

        next_level: list[str] = []

        for batch in batches:
            batch_text = "\n\n".join(batch)

            summary = await summarize_batch(batch_text)

            if not summary.strip():
                raise ValueError("LLM returned an empty summary.")

            next_level.append(summary)

        current = next_level

    return current[0]