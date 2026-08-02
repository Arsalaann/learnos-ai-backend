from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.workspace_service import get_workspace_by_id


def get_current_workspace(workspace_id: int = Path(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    workspace = get_workspace_by_id(db, workspace_id)

    if workspace.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace.",
        )

    return workspace