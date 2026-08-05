import secrets


def build_untrusted_context(sections: dict[str, str]) -> str:
    boundary = secrets.token_hex(32)

    content = "\n\n".join(
        f"{name.upper()}:\n{value}"
        for name, value in sections.items()
    )

    return (
        f"BEGIN_UNTRUSTED_DATA_{boundary}\n\n"
        f"{content}\n\n"
        f"END_UNTRUSTED_DATA_{boundary}"
    )
    
    


    
from app.llm.mappers import to_conversation_text
from app.services.conversation_service import ConversationContext


def build_conversation_context_text(
    context: ConversationContext,
) -> dict[str, str]:
    sections: dict[str, str] = {}

    if context.summary:
        sections["previous_conversation_summary"] = context.summary

    if context.messages:
        messages = to_conversation_text(context.messages)

        sections["new_conversation_messages"] = "\n".join(
            f"{message.role.value}: {message.content}"
            for message in messages
        )

    return sections