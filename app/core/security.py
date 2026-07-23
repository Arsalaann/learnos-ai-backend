from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException

from app.core.config import settings

 
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM])
        if "sub" not in payload:
            raise HTTPException(status_code=401,detail="Could not validate credentials")
        return payload
    except JWTError:
        raise HTTPException(status_code=401,detail="Could not validate credentials")
    

def hash_password(password: str) -> str:
    return PasswordHash.recommended().hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return PasswordHash.recommended().verify(password, hashed_password)