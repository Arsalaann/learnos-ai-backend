from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Conversation,
    ConversationType,
    Document,
    DocumentArtifact,
    Message,
    User,
    Workspace,
)
from app.services.document_artifact_service import (
    find_latest_conversation_quiz,
    find_latest_conversation_summary,
)
from app.services.message_repository import get_messages, get_messages_after


@dataclass
class ConversationContext:
    summary: DocumentArtifact | None
    messages: list[Message]
    
    
    
    

def _validate_conversation_creation(
    conversation_type: ConversationType,
    document: Document | None,
) -> None:

    if conversation_type == ConversationType.WORKSPACE and document is not None:
        raise ValueError(
            "Workspace conversations cannot have a document."
        )

    if conversation_type == ConversationType.DOCUMENT and document is None:
        raise ValueError(
            "Document conversations must have a document."
        )




def _ensure_workspace_conversation(
    conversation: Conversation,
) -> None:

    if conversation.conversation_type != ConversationType.WORKSPACE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operation is only supported for workspace conversations.",
        )
        
        
def _find_document_conversation(
    db: Session,
    workspace: Workspace,
    document: Document,
) -> Conversation | None:

    statement = (
        select(Conversation)
        .where(
            Conversation.workspace_id == workspace.id,
            Conversation.document_id == document.id,
            Conversation.conversation_type == ConversationType.DOCUMENT,
        )
    )

    result = db.execute(statement)

    return result.scalar_one_or_none()






def get_conversation_context(
    db: Session,
    document: Document,
    conversation: Conversation,
) -> ConversationContext:
    latest_summary = find_latest_conversation_summary(
        db=db,
        document=document,
        conversation=conversation,
    )

    if latest_summary is None or latest_summary.source_message_id is None:
        messages = get_messages(
            db=db,
            conversation=conversation,
        )
    else:
        messages = get_messages_after(
            db=db,
            conversation=conversation,
            message_id=latest_summary.source_message_id,
        )

    return ConversationContext(
        summary=latest_summary,
        messages=messages,
    )
    
    
    
    
def get_quiz_context_messages(
    db: Session,
    document: Document,
    conversation: Conversation,
) -> list[Message]:
    latest_quiz = find_latest_conversation_quiz(
        db=db,
        document=document,
        conversation=conversation,
    )

    if latest_quiz is None or latest_quiz.source_message_id is None:
        return get_messages(
            db=db,
            conversation=conversation,
        )

    return get_messages_after(
        db=db,
        conversation=conversation,
        message_id=latest_quiz.source_message_id,
    )
    
    
    

        
def get_document_conversation(
    db: Session,
    workspace: Workspace,
    document: Document,
) -> Conversation:

    conversation = _find_document_conversation(
        db=db,
        workspace=workspace,
        document=document,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document conversation not found.",
        )

    return conversation
        
        
        
        
        
        
        
        
        
def get_workspace_conversations(
    db: Session,
    workspace: Workspace,
) -> list[Conversation]:

    statement = (
        select(Conversation)
        .where(
            Conversation.workspace_id == workspace.id,
            Conversation.conversation_type == ConversationType.WORKSPACE,
        )
        .order_by(Conversation.updated_at.desc())
    )

    result = db.execute(statement)

    return result.scalars().all()





def get_current_conversation(
    db: Session,
    current_user: User,
    conversation_id: int,
) -> Conversation:

    statement = (
        select(Conversation)
        .join(
            Workspace,
            Workspace.id == Conversation.workspace_id,
        )
        .where(
            Conversation.id == conversation_id,
            Workspace.user_id == current_user.id,
        )
    )

    result = db.execute(statement)

    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return conversation






def create_document_conversation(
    db: Session,
    workspace: Workspace,
    document: Document,
) -> Conversation:

    _validate_conversation_creation(
        conversation_type=ConversationType.DOCUMENT,
        document=document,
    )

    conversation = Conversation(
        workspace_id=workspace.id,
        document_id=document.id,
        conversation_type=ConversationType.DOCUMENT,
        title=document.original_filename,
    )

    db.add(conversation)
    db.flush()

    return conversation

def _ensure_workspace_chat_allowed(workspace: Workspace) -> None:
    if workspace.is_default:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The default workspace does not support workspace conversations.")

def create_workspace_conversation(
    db: Session,
    workspace: Workspace,
    title: str | None = None,
) -> Conversation:
    _ensure_workspace_chat_allowed(workspace)
    conversation = _create_conversation(
        db=db,
        workspace=workspace,
        conversation_type=ConversationType.WORKSPACE,
        title=title or "New Chat",
    )

    db.commit()
    db.refresh(conversation)

    return conversation



def rename_conversation(
    db: Session,
    conversation: Conversation,
    title: str,
) -> Conversation:
    
    _ensure_workspace_conversation(conversation)

    if conversation.conversation_type == ConversationType.DOCUMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document conversations cannot be renamed.",
        )

    conversation.title = title.strip()

    db.commit()
    db.refresh(conversation)

    return conversation


def delete_conversation(
    db: Session,
    conversation: Conversation,
) -> None:

    _ensure_workspace_conversation(conversation)
    
    if conversation.conversation_type == ConversationType.DOCUMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document conversations cannot be deleted.",
        )

    db.delete(conversation)

    db.commit()


def _create_conversation(
    db: Session,
    workspace: Workspace,
    conversation_type: ConversationType,
    title: str,
    document: Document | None = None,
) -> Conversation:

    _validate_conversation_creation(
        conversation_type=conversation_type,
        document=document,
    )

    if conversation_type == ConversationType.WORKSPACE and workspace.is_default:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The default workspace does not support workspace conversations.")
                            
    conversation = Conversation(
        workspace_id=workspace.id,
        document_id=document.id if document else None,
        conversation_type=conversation_type,
        title=title,
    )

    db.add(conversation)
    db.flush()

    return conversation