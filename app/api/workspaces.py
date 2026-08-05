from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import get_current_workspace
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.services.workspace_service import (
    create_workspace,
    delete_workspace,
    find_workspace_by_title,
    get_workspaces,
    update_workspace,
)

router = APIRouter()


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def register_workspace(workspace_data: WorkspaceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing_workspace = find_workspace_by_title(db, current_user, workspace_data.title)

    if existing_workspace is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Workspace already exists.",
        )
        
    return create_workspace(db, current_user, workspace_data)


@router.get("/", response_model=list[WorkspaceResponse])
def get_all_workspaces(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_workspaces(db, current_user)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace: Workspace = Depends(get_current_workspace)):
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace_endpoint(workspace_update: WorkspaceUpdate, workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db)):
    return update_workspace(db, workspace, workspace_update)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace_endpoint(workspace: Workspace = Depends(get_current_workspace), db: Session = Depends(get_db)):
    delete_workspace(db, workspace)













