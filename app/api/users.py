from fastapi import APIRouter, Depends, status

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse,UserUpdate,UserLogin
from app.schemas.auth import TokenResponse
from app.services.user_service import create_user, get_user_by_id,update_current_user
from app.services.auth_service import authenticate_user, get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate,db: Session = Depends(get_db)):
    return create_user(db, user_data)

@router.post("/login",response_model=TokenResponse)
def login_user(user_credentials: UserLogin,db: Session = Depends(get_db)):
    return authenticate_user(db, user_credentials)

@router.get("/me", response_model=UserResponse) 
def get_me(current_user: User = Depends(get_current_user)): 
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_me(user_update: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return update_current_user(db, current_user, user_update)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int,db: Session = Depends(get_db)):
    return get_user_by_id(db, user_id)

