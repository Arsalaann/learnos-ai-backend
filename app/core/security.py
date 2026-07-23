from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC
import os
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        if "sub" not in payload:
            raise HTTPException(status_code=401,detail="Could not validate credentials")
        return payload
    except JWTError:
        raise HTTPException(status_code=401,detail="Could not validate credentials")
    

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)