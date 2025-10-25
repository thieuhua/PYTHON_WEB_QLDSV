import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, Request  # Thêm Request
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
        token = token.strip("\"")
        print("Decoding token:", token)
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        print("payload", payload)
        return payload
    except JWTError as e:
        print("JWTError:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def hash_password(password: str) -> str:
    return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

def create_token(data: dict):
    return jwt.encode(data, JWT_SECRET, algorithm=ALGORITHM)

def decode_tokenNE(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Thêm hàm verify_token (thay thế cho hàm bị lỗi)
def verify_token(token: str):
    """Hàm verify_token thay thế cho hàm cũ bị lỗi"""
    return decode_tokenNE(token)

async def auth_request(request: Request = None, token: str = None):
    """Xử lý auth từ request hoặc token trực tiếp"""
    if request and not token:
        # Lấy token từ request
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split("Bearer ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify token sử dụng hàm decode_tokenNE
    user = decode_tokenNE(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user