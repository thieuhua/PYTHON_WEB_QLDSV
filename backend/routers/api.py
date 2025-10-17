from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from . import schemas
from ..db import crud, models, database
from . import jwt_auth
router = APIRouter()

class UserAuth(BaseModel):
    username: str
    password: str

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(user: UserAuth, db: Session = Depends(get_db)):
    hashedpassw:str =jwt_auth.hash_password(user.password)
    user_db =schemas.UserCreate(username=user.username, password= hashedpassw)
    try:
        crud.create_user(db, user_db)
    except Exception as e:
        print("❌ Lỗi khi tạo user:", e)
        raise HTTPException(400) # Bad request
    token = jwt_auth.create_token({"username":user_db.username, "password": user_db.password})
    return token

@router.post("/login")
def login(user:UserAuth, db: Session = Depends(get_db)):
    print("user:", user.username, user.password)
    user_db :schemas.UserOut = crud.get_user_by_username(db, user.username)
    ok =jwt_auth.verify_password(user.password, user_db.password)
    if not ok: 
        raise HTTPException(401) # Unauthorized
    
    token = jwt_auth.create_token({"username":user_db.username, "id": user_db.id})
    print("Generated token:", token)
    return token

@router.get("/me")
def getMe(user :dict=Depends(jwt_auth.auth), db: Session = Depends(get_db)):
    # userinf  = schemas.UserBase(crud.get_user_by_username(db, user['username']))
    db_user  = crud.get_user_by_username(db, user['username'])
    userinf = schemas.UserBase(
        username=db_user.username,
        role=db_user.role,
        name=db_user.name
    )
    return userinf.__dict__