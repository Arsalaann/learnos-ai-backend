from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Conversation, Message


def get_message_by_id(
    db: Session,
    conversation: Conversation,
    message_id: int,
) -> Message:

    statement = (
        select(Message)
        .where(
            Message.id == message_id,
            Message.conversation_id == conversation.id,
        )
    )

    result = db.execute(statement)

    message = result.scalar_one_or_none()

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found.",
        )

    return message


def delete_message(
    db: Session,
    conversation: Conversation,
    message_id: int,
) -> None:

    message = get_message_by_id(
        db=db,
        conversation=conversation,
        message_id=message_id,
    )

    db.delete(message)

    db.commit()

def get_messages(
    db: Session,
    conversation: Conversation,
) -> list[Message]:
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.asc())
        .options(selectinload(Message.artifact))
    )

    result = db.execute(statement)

    return result.scalars().all()



def get_message(
    db: Session,
    message_id: int,
) -> Message:
    statement = (
        select(Message)
        .where(Message.id == message_id)
        .options(selectinload(Message.artifact))
    )

    result = db.execute(statement)

    return result.scalar_one()




def get_messages_after(
    db: Session,
    conversation: Conversation,
    message_id: int,
) -> list[Message]:
    statement = (
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.id > message_id,
        )
        .order_by(Message.id.asc())
    )

    result = db.execute(statement)

    return result.scalars().all()