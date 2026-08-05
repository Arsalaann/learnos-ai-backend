from app.llm.builders.context import build_untrusted_context
from app.llm.config import CHAT_MAX_OUTPUT_TOKENS, CHAT_TEMPERATURE
from app.llm.mappers import to_conversation_text
from app.llm.prompts import CHAT_INSTRUCTIONS, SYSTEM_PROMPT
from app.llm.schemas import LLMMessage, LLMRequest, MessageRole


def build_chat_request(
    context: str,
    conversation: list[LLMMessage],
    stream: bool = False,
) -> LLMRequest:
    conversation_text = to_conversation_text(conversation)

    untrusted_context = build_untrusted_context(
        {
            "document": context,
            "conversation": conversation_text,
        }
    )

    return LLMRequest(
        messages=[
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=f"{SYSTEM_PROMPT}\n\n{CHAT_INSTRUCTIONS}",
            ),
            LLMMessage(
                role=MessageRole.USER,
                content=untrusted_context,
            ),
        ],
        temperature=CHAT_TEMPERATURE,
        max_output_tokens=CHAT_MAX_OUTPUT_TOKENS,
        stream=stream,
    )