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
        token =token.strip("\"")
        print("Decoding token:", token)
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        print("payload",payload)
        return payload
    except JWTError as e:
        print("JWTError:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_password(plain_password: str, hashed_password:str) ->bool:
    return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    # return checkpw(plain_password, hashed_password)

def hash_password(password: str) -> str:
    # return hashpw(password, gensalt())
    return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

def create_token(data: dict):
    return jwt.encode(data, JWT_SECRET, algorithm=ALGORITHM)

def decode_tokenNE(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None