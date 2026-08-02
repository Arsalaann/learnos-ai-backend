from fastapi import APIRouter, Depends, status

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.workspace import get_current_workspace
from app.models.workspace import Workspace
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message_service import create_message, get_messages, delete_message

router = APIRouter()


@router.post("/{workspace_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message_endpoint(message: MessageCreate, workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db)):
    return create_message(db, workspace, message.content, message.document_id)


@router.get("/{workspace_id}/messages", response_model=list[MessageResponse])
def get_messages_endpoint(context_document_id: int | None = None, workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db)):
    return get_messages(db, workspace, context_document_id)


@router.delete("/{workspace_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message_endpoint(message_id: int, workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db)):
    delete_message(db, message_id, workspace)