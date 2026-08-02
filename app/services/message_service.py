from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message, MessageRole
from app.models.workspace import Workspace


def find_message_by_id(db: Session, message_id: int):

    statement = select(Message).where(Message.id == message_id)

    result = db.execute(statement)

    return result.scalar_one_or_none()


def get_message_by_id(db: Session, message_id: int):

    message = find_message_by_id(db, message_id)

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found.",
        )

    return message


def get_messages(db: Session, workspace: Workspace, context_document_id: int | None = None):

    statement = select(Message).where(Message.workspace_id == workspace.id)

    if context_document_id is not None:
        statement = statement.where(Message.document_id == context_document_id)

    statement = statement.order_by(Message.created_at.asc())

    result = db.execute(statement)

    return result.scalars().all()


def create_message(db: Session, workspace: Workspace, content: dict, document_id: int | None):

    message = Message(
        workspace_id=workspace.id,
        document_id=document_id,
        role=MessageRole.USER,
        content=content,
    )

    db.add(message)

    db.commit()
    db.refresh(message)

    return message

def delete_message(db: Session, message_id: int, workspace: Workspace):

    message = get_message_by_id(db, message_id)

    if message.workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found.",
        )

    db.delete(message)

    db.commit()