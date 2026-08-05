from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.conversation import get_conversation
from app.dependencies.workspace import get_current_workspace
from app.models.conversation import Conversation
from app.models.workspace import Workspace
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from app.services.conversation_service import (
    create_workspace_conversation,
    delete_conversation,
    get_workspace_conversations,
    rename_conversation,
)

router = APIRouter()








@router.get( "/{workspace_id}/conversations", response_model=list[ConversationResponse], )
def get_workspace_conversations_endpoint( workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db), ):
    return get_workspace_conversations(db, workspace)



@router.post( "/{workspace_id}/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED, )
def create_workspace_conversation_endpoint( conversation_data: ConversationCreate,workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db), ):
    return create_workspace_conversation(db, workspace, title=conversation_data.title)


@router.patch( "/{workspace_id}/conversations/{conversation_id}", response_model=ConversationResponse, )
def rename_conversation_endpoint( conversation_update: ConversationUpdate, conversation: Conversation = Depends(get_conversation), db: Session = Depends(get_db), ):
    return rename_conversation( db=db, conversation=conversation, title=conversation_update.title, )


@router.delete( "/{workspace_id}/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, )
def delete_conversation_endpoint( conversation: Conversation = Depends(get_conversation), db: Session = Depends(get_db), ):
    delete_conversation( db=db, conversation=conversation, )
