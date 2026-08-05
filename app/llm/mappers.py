from app.llm.schemas import LLMMessage
from app.models import Message
from app.models.message import MessageType


def get_message_text(message: Message) -> str:
    if message.message_type == MessageType.TEXT:
        return message.content["text"]

    if message.message_type == MessageType.QUIZ:
        return "[Assistant generated a quiz.]"

    if message.message_type == MessageType.FLASHCARDS:
        return "[Assistant generated flashcards.]"

    return ""

def to_conversation_text(messages: list[Message]) -> list[LLMMessage]:
    return [ LLMMessage( role=message.role, content=get_message_text(message) ) for message in messages ]