from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import schemas
from ..db import crud, models, database
from . import jwt_auth
router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    hashedpassw =jwt_auth.hash_password(password)
    user =schemas.UserCreate(username=username, password= hashedpassw)
    try:
        crud.create_user(db, )
    except:
        raise HTTPException(400)
    token = jwt_auth.create_token({"username":user.username, "password": user.password})
    return token

@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user :schemas.UserCreate = crud.get_user_by_username(db, username)
    ok =jwt_auth.verify_password(password, user.password)
    if not ok: 
        raise HTTPException(401)
    
    token = jwt_auth.create_token({"username":user.username, "password": user.password})
    return token

@router.get("/me")
def getMe(user :dict=Depends(jwt_auth.auth), db: Session = Depends(get_db)):
    userinf  =schemas.UserBase(crud.get_user_by_username(db, user.name))
    return userinf.__dict__()