from app.llm.builders.context import build_untrusted_context
from app.llm.config import SUMMARY_MAX_OUTPUT_TOKENS, SUMMARY_TEMPERATURE
from app.llm.prompts import (
    CONVERSATION_BATCH_SUMMARY_INSTRUCTIONS,
    CONVERSATION_SUMMARY_INSTRUCTIONS,
    CONVERSATION_SUMMARY_REDUCTION_INSTRUCTIONS,
    CONVERSATION_SUMMARY_REGENERATION_INSTRUCTIONS,
    DOCUMENT_SUMMARY_INSTRUCTIONS,
    DOCUMENT_SUMMARY_REDUCTION_INSTRUCTIONS,
    SYSTEM_PROMPT,
    TOPIC_CONSOLIDATION_INSTRUCTIONS,
)
from app.llm.schemas import LLMMessage, LLMRequest, MessageRole
from app.llm.structured import build_json_schema_response_format
from app.schemas.document_artifact import (
    DocumentTopic,
    DocumentTopicsResponse,
    SummaryBatchResponse,
)


def build_document_summary_request(
    content: str,
) -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    f"{SYSTEM_PROMPT}\n\n"
                    f"{DOCUMENT_SUMMARY_INSTRUCTIONS}"
                ),
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=build_untrusted_context(
                    {"document": content}
                ),
            ),
        ],
        temperature=SUMMARY_TEMPERATURE,
        max_output_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
        response_format=build_json_schema_response_format(
            SummaryBatchResponse,
        ),
    )


def build_document_summary_reduction_request(
    summaries: str,
) -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=f"{SYSTEM_PROMPT}\n\n{DOCUMENT_SUMMARY_REDUCTION_INSTRUCTIONS}",
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=build_untrusted_context(
                    {"summaries": summaries}
                ),
            ),
        ],
        temperature=SUMMARY_TEMPERATURE,
        max_output_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
    )
    
    
def build_topic_consolidation_request(
    topics: list[DocumentTopic],
) -> LLMRequest:
    topics_text = "\n".join(
        (
            f"- {topic.name}\n"
            + "\n".join(
                f"  - {subtopic}"
                for subtopic in topic.subtopics
            )
        )
        for topic in topics
    )

    return LLMRequest(
        messages=[
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    f"{SYSTEM_PROMPT}\n\n"
                    f"{TOPIC_CONSOLIDATION_INSTRUCTIONS}"
                ),
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=build_untrusted_context(
                    {"topics": topics_text}
                ),
            ),
        ],
        temperature=SUMMARY_TEMPERATURE,
        max_output_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
        response_format=build_json_schema_response_format(
            DocumentTopicsResponse,
        ),
    )
    

def build_conversation_batch_summary_request(
    messages: str,
) -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    f"{SYSTEM_PROMPT}\n\n"
                    f"{CONVERSATION_BATCH_SUMMARY_INSTRUCTIONS}"
                ),
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=build_untrusted_context(
                    {"new_conversation_messages": messages}
                ),
            ),
        ],
        temperature=SUMMARY_TEMPERATURE,
        max_output_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
    )


def build_conversation_summary_reduction_request(
    summaries: str,
) -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    f"{SYSTEM_PROMPT}\n\n"
                    f"{CONVERSATION_SUMMARY_REDUCTION_INSTRUCTIONS}"
                ),
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=build_untrusted_context(
                    {"conversation_summaries": summaries}
                ),
            ),
        ],
        temperature=SUMMARY_TEMPERATURE,
        max_output_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
    )



def build_conversation_summary_regeneration_request(
    summary: str,
) -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    f"{SYSTEM_PROMPT}\n\n"
                    f"{CONVERSATION_SUMMARY_REGENERATION_INSTRUCTIONS}"
                ),
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=build_untrusted_context(
                    {"conversation_summary": summary}
                ),
            ),
        ],
        temperature=SUMMARY_TEMPERATURE,
        max_output_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
    )
    
    

def build_conversation_summary_request(
    document_summary: str,
    new_conversation_summary: str,
) -> LLMRequest:
    sections = {
        "document_summary": document_summary,
        "conversation_activity": new_conversation_summary,
    }

    return LLMRequest(
        messages=[
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    f"{SYSTEM_PROMPT}\n\n"
                    f"{CONVERSATION_SUMMARY_INSTRUCTIONS}"
                ),
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=build_untrusted_context(sections),
            ),
        ],
        temperature=SUMMARY_TEMPERATURE,
        max_output_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
    )