from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, MeResponse
from app.core.security import hash_password

from app.services.workspace_service import get_workspaces


def find_user_by_id(db: Session, user_id: int):
    statement = select(User).where(User.id == user_id)
    result = db.execute(statement)
    return result.scalar_one_or_none()

def find_user_by_email(db: Session, email: str):
    statement = select(User).where(User.email == email)
    result = db.execute(statement)
    return result.scalar_one_or_none()

def get_user_by_id(db: Session, user_id: int):
    user = find_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    return user


def get_me(db: Session, current_user: User):
    workspaces = get_workspaces(db, current_user)
    return MeResponse(
        full_name=current_user.full_name,
        workspaces=workspaces,
    )

def create_user(db: Session, user_data: UserCreate):
    hashed_password = hash_password(user_data.password)
    user = User(full_name=user_data.full_name,email=user_data.email,hashed_password=hashed_password)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException( status_code=status.HTTP_409_CONFLICT,detail="Email already exists")
    db.refresh(user)
    return user

def update_current_user(db: Session, current_user: User, user_update: UserUpdate):
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            setattr(current_user, "hashed_password", hash_password(value))
        else:
            setattr(current_user, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Email already exists")
    db.refresh(current_user)
    return current_user
        
        