from sqlalchemy.orm import Session

from fastapi import HTTPException
from starlette import status

from app.models.user import User
from app.schemas.user import UserLogin
from app.services.user_service import find_user_by_email,get_user_by_id
from app.core.security import verify_password,create_access_token,verify_access_token
import logging

logger = logging.getLogger(__name__)

def authenticate_user(db: Session, credentials: UserLogin):
    user = find_user_by_email(db, credentials.email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Failed login for {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": str(user.id)})
    user.access_token = access_token
    logger.info(f"User {user.email} authenticated successfully.")
    return {"access_token": access_token,"token_type": "bearer"}

def load_current_user(db: Session, token: str) -> User:
    payload = verify_access_token(token)
    user_id = int(payload["sub"])
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials")
    return user