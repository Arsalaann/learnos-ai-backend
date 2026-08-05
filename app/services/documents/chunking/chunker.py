from dataclasses import dataclass

from app.embeddings.service import EmbeddingService
from app.services.documents.constants import (
    MAX_TOKENS,
    MIN_TOKENS,
    OVERLAP_TOKENS,
    TARGET_TOKENS,
)
from app.services.documents.extraction.models import ExtractedBlock


@dataclass(slots=True)
class Chunk:
    index: int
    content: str
    source_type: str
    source_start: int | None
    source_end: int | None
    
    
def split_large_block(
    block: ExtractedBlock,
    embedding_service: EmbeddingService,
    start_index: int,
) -> list[Chunk]:

    tokens = embedding_service.encode_tokens(
        block.text
    )

    chunks: list[Chunk] = []

    start = 0

    while start < len(tokens):

        end = min(
            start + MAX_TOKENS,
            len(tokens),
        )

        chunk_tokens = tokens[start:end]

        content = embedding_service.decode_tokens(
            chunk_tokens
        ).strip()

        if content:

            chunks.append(
                Chunk(
                    index=start_index + len(chunks),
                    content=content,
                    source_type=block.source_type,
                    source_start=block.source_start,
                    source_end=block.source_end,
                )
            )

        if end >= len(tokens):
            break

        start = end - OVERLAP_TOKENS

    return chunks




def build_overlap_text(
    current_blocks: list[ExtractedBlock],
    embedding_service: EmbeddingService,
) -> str:

    content = "\n\n".join(
        block.text.strip()
        for block in current_blocks
        if block.text.strip()
    )

    tokens = embedding_service.encode_tokens(content)

    if len(tokens) <= OVERLAP_TOKENS:
        return content

    overlap_tokens = tokens[-OVERLAP_TOKENS:]

    return embedding_service.decode_tokens(
        overlap_tokens
    ).strip()
    
    
    
def token_count(
    text: str,
    embedding_service: EmbeddingService,
) -> int:

    return embedding_service.count_tokens(text)



def reindex_chunks(
    chunks: list[Chunk],
) -> list[Chunk]:

    return [
        Chunk(
            index=index,
            content=chunk.content,
            source_type=chunk.source_type,
            source_start=chunk.source_start,
            source_end=chunk.source_end,
        )
        for index, chunk in enumerate(chunks)
    ]
    
    
    
    
    
    
def build_chunk(
    blocks: list[ExtractedBlock],
    index: int,
) -> Chunk:

    content_blocks = [
        block
        for block in blocks
        if block.type != "context"
    ]

    content = "\n\n".join(
        block.text.strip()
        for block in blocks
        if block.text.strip()
    )

    source_blocks = [
        block
        for block in content_blocks
        if block.source_start is not None
    ]

    if not source_blocks:
        source_type = "overlap"
        source_start = None
        source_end = None

    else:
        source_types = {
            block.source_type
            for block in source_blocks
        }

        source_type = (
            next(iter(source_types))
            if len(source_types) == 1
            else "mixed"
        )

        source_start = min(
            block.source_start
            for block in source_blocks
            if block.source_start is not None
        )

        source_end = max(
            block.source_end
            for block in source_blocks
            if block.source_end is not None
        )

    return Chunk(
        index=index,
        content=content,
        source_type=source_type,
        source_start=source_start,
        source_end=source_end,
    )





def chunk_blocks(
    blocks: list[ExtractedBlock],
    embedding_service: EmbeddingService,
) -> list[Chunk]:

    if not blocks:
        return []

    chunks: list[Chunk] = []

    current_blocks: list[ExtractedBlock] = []
    current_tokens = 0
    current_heading: ExtractedBlock | None = None

    for block in blocks:

        if block.type == "heading":
            current_heading = block
            continue

        block_text = block.text.strip()

        if not block_text:
            continue

        block_tokens = embedding_service.count_tokens(block_text)

        if current_heading is not None:
            heading_tokens = embedding_service.count_tokens(
                current_heading.text
            )

            if (
                current_blocks
                and current_tokens + heading_tokens + block_tokens > TARGET_TOKENS
            ):
                chunks.append(
                    build_chunk(
                        blocks=current_blocks,
                        index=len(chunks),
                    )
                )

                current_blocks = []
                current_tokens = 0

            if not current_blocks:
                current_blocks.append(current_heading)
                current_tokens += heading_tokens

            current_heading = None

        if block_tokens > MAX_TOKENS:

            if current_blocks:
                chunks.append(
                    build_chunk(
                        blocks=current_blocks,
                        index=len(chunks),
                    )
                )

                current_blocks = []
                current_tokens = 0

            chunks.extend(
                split_large_block(
                    block=block,
                    embedding_service=embedding_service,
                    start_index=len(chunks),
                )
            )

            continue

        if (
            current_blocks
            and current_tokens + block_tokens > TARGET_TOKENS
        ):
            chunks.append(
                build_chunk(
                    blocks=current_blocks,
                    index=len(chunks),
                )
            )

            overlap_text = build_overlap_text(
                current_blocks=current_blocks,
                embedding_service=embedding_service,
            )

            current_blocks = []

            if overlap_text:
                overlap_block = ExtractedBlock(
                    index=-1,
                    type="context",
                    text=overlap_text,
                    source_type="overlap",
                    source_start=None,
                    source_end=None,
                )

                current_blocks.append(overlap_block)

                current_tokens = embedding_service.count_tokens(
                    overlap_text
                )

            else:
                current_tokens = 0

        current_blocks.append(block)
        current_tokens += block_tokens

    if current_blocks:
        final_chunk = build_chunk(
            blocks=current_blocks,
            index=len(chunks),
        )

        if (
            chunks
            and token_count(
                final_chunk.content,
                embedding_service,
            ) < MIN_TOKENS
        ):
            previous = chunks[-1]

            merged_content = (
                previous.content
                + "\n\n"
                + final_chunk.content
            )

            merged_tokens = token_count(
                merged_content,
                embedding_service,
            )

            if merged_tokens <= MAX_TOKENS:
                chunks[-1] = Chunk(
                    index=previous.index,
                    content=merged_content,
                    source_type=previous.source_type,
                    source_start=previous.source_start,
                    source_end=final_chunk.source_end,
                )

            else:
                chunks.append(final_chunk)
        else:
            chunks.append(final_chunk)

    return reindex_chunks(chunks)