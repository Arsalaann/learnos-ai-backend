from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import Conversation, User
from app.services.conversation_service import get_current_conversation


def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Conversation:

    return get_current_conversation(
        db=db,
        current_user=current_user,
        conversation_id=conversation_id,
    )