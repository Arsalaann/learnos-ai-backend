from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import oauth2_scheme
from app.services.auth_service import load_current_user


def get_current_user(token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    return load_current_user(db, token)