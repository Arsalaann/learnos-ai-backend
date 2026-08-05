from app.llm.builders.context import build_untrusted_context
from app.llm.config import QUIZ_MAX_OUTPUT_TOKENS, QUIZ_TEMPERATURE
from app.llm.mappers import to_conversation_text
from app.llm.prompts import QUIZ_INSTRUCTIONS, SYSTEM_PROMPT
from app.llm.schemas import LLMMessage, LLMRequest, MessageRole
from app.llm.structured import build_json_schema_response_format
from app.models import Message
from app.schemas.document_artifact import QuizResponse


def build_quiz_request(
    document_text: str,
    conversation_summary: str | None,
    conversation: list[Message],
) -> LLMRequest:
    conversation_text = to_conversation_text(conversation)

    untrusted_context = build_untrusted_context(
        {
            "document": document_text,
            "conversation_summary": conversation_summary or "",
            "conversation": conversation_text,
        }
    )

    return LLMRequest(
        messages=[
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=f"{SYSTEM_PROMPT}\n\n{QUIZ_INSTRUCTIONS}",
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=untrusted_context,
            ),
        ],
        temperature=QUIZ_TEMPERATURE,
        max_output_tokens=QUIZ_MAX_OUTPUT_TOKENS,
        response_format=build_json_schema_response_format(QuizResponse),
    )