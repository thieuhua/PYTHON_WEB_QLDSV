import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from bcrypt import checkpw, hashpw, gensalt
# load .env
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "defaultsecret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def auth(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_password(plain_password, hashed_password):
    return checkpw(plain_password, hashed_password)

def hash_password(password):
    return hashpw(password, gensalt())

def create_token(data: dict):
    return jwt.encode(data, JWT_SECRET, algorithm=ALGORITHM)

def decode_tokenNE(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None