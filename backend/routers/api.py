from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import schemas
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
    hashedpassw: str = jwt_auth.hash_password(user.password)
    user_db = schemas.UserCreate(username=user.username, password=hashedpassw, full_name= "NoName")
    try:
        crud.create_user(db, user_db)
    except Exception as e:
        print("Lỗi khi tạo user:", e)
        raise HTTPException(400) # Bad request
    
    token = jwt_auth.create_token({"username": user_db.username, "password": user_db.password})
    
    return {
        "token": token, 
        "message": "Đăng ký thành công",
        "username": user.username
    }

@router.post("/login")
def login(user: UserAuth, db: Session = Depends(get_db)):
    print("user:", user.username, user.password)
    user_db = crud.get_user_by_username(db, user.username)
    ok = jwt_auth.verify_password(user.password, user_db.password)
    if not ok: 
        raise HTTPException(401) # Unauthorized
    
    token = jwt_auth.create_token({"username": user_db.username, "id": user_db.user_id})
    print("Generated token:", token)
    
    # SỬA: Trả về JSON thay vì text
    return {
        "token": token, 
        "message": "Đăng nhập thành công",
        "username": user.username
    }

@router.get("/me", response_model=schemas.UserRead)
def getMe(user: dict = Depends(jwt_auth.auth), db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, user['username'])
    if not db_user:
        raise HTTPException(404, detail="User not found")
    return db_user

class UpdateRoleRequest(BaseModel):
    username: str
    new_role: str

@router.post("/admin/update-role")
def update_user_role(role_data: UpdateRoleRequest, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, role_data.username)
    if not db_user:
        raise HTTPException(404, detail="User not found")
    
    # Validate role
    if role_data.new_role not in ["admin", "teacher", "student"]:
        raise HTTPException(400, detail="Invalid role")
    
    db_user.role = role_data.new_role
    db.commit()
    db.refresh(db_user)
    
    return {"message": f"Đã cập nhật role {role_data.new_role} cho user {role_data.username}"}

@router.get("/debug-all-users")
def debug_all_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    result = []
    for user in users:
        result.append({
            "id": user.user_id,
            "username": user.username,
            "role": user.role.value if user.role else None,
            "name": user.full_name
        })
    return result
@router.get("/check-auth")
def check_auth(user: dict = Depends(jwt_auth.auth)):
    return {"authenticated": True, "user": user}