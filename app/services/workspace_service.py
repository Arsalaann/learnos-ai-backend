from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate

from app.services.documents.storage import delete_workspace_uploads

def find_workspace_by_title(db: Session, current_user: User, title: str):

    statement = (
        select(Workspace)
        .where(Workspace.user_id == current_user.id)
        .where(Workspace.title == title)
    )

    result = db.execute(statement)

    return result.scalar_one_or_none()


def find_workspace_by_id(db: Session, workspace_id: int):

    statement = select(Workspace).where(Workspace.id == workspace_id)

    result = db.execute(statement)

    return result.scalar_one_or_none()


def get_workspace_by_id(db: Session, workspace_id: int):

    workspace = find_workspace_by_id(db, workspace_id)

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    return workspace


def get_workspaces(db: Session, current_user: User):

    statement = (
        select(Workspace)
        .where(Workspace.user_id == current_user.id)
        .order_by(Workspace.updated_at.desc())
    )

    result = db.execute(statement)

    return result.scalars().all()


def create_workspace(db: Session, current_user: User, workspace_data: WorkspaceCreate):

    workspace = Workspace(
        user_id=current_user.id,
        title=workspace_data.title,
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return workspace


def update_workspace(db: Session, workspace: Workspace, workspace_update: WorkspaceUpdate):

    update_data = workspace_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(workspace, field, value)

    db.commit()
    db.refresh(workspace)

    return workspace


def delete_workspace(db: Session, workspace: Workspace):
    workspace_id = workspace.id
    db.delete(workspace)
    db.commit()
    delete_workspace_uploads(workspace_id)