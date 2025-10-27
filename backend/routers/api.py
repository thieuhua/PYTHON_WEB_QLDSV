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
    # data = update.dict(exclude_unset=True)
    data = update.model_dump(exclude_unset=True)

    # Password handling
    if 'password' in data and data['password']:
        db_user.password = jwt_auth.hash_password(data.pop('password'))

    # Update simple user fields
    for field in ['full_name', 'email', 'role']:
        if field in data:
            setattr(db_user, field, data.pop(field))

    # Handle student profile
    # Determine effective role (new role if provided, else existing)
    effective_role = getattr(db_user.role, 'value', db_user.role) if hasattr(db_user.role, 'value') else db_user.role
    if 'role' in update.__fields_set__:
        # if role was changed in update, re-evaluate effective_role
        effective_role = update.role.value if hasattr(update.role, 'value') else update.role

    if str(effective_role) == 'student':
        student = crud.get_student(db, db_user.user_id)
        if student:
            if 'birthdate' in data:
                student.birthdate = data.pop('birthdate')
        else:
            # create student; student_code optional — generate fallback if not provided
            student_code = data.pop('student_code', None) if 'student_code' in data else None
            if not student_code:
                student_code = f"ST{db_user.user_id:04d}"
            sc = schemas.StudentCreate(user_id=db_user.user_id, student_code=student_code, birthdate=data.pop('birthdate', None))
            try:
                crud.create_student(db, sc)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to create student profile: {e}")

    # Handle teacher profile
    if str(effective_role) == 'teacher':
        teacher = crud.get_teacher(db, db_user.user_id)
        if teacher:
            if 'department' in data:
                teacher.department = data.pop('department')
            if 'title' in data:
                teacher.title = data.pop('title')
        else:
            tc = schemas.TeacherCreate(user_id=db_user.user_id, department=data.pop('department', None), title=data.pop('title', None))
            try:
                crud.create_teacher(db, tc)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to create teacher profile: {e}")

    # Commit changes
    db.commit()
    db.refresh(db_user)
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

# ==============================================================
# THÊM 3 API ENDPOINTS NÀY VÀO CUỐI FILE api.py
# ==============================================================

@router.get("/students/{student_id}/enrollments", response_model=list[schemas.EnrollmentRead])
def get_student_enrollments_api(student_id: int, db: Session = Depends(get_db)):
    """Lấy danh sách các lớp học mà sinh viên đã đăng ký"""
    enrollments = crud.get_student_enrollments(db, student_id)
    return enrollments


@router.get("/classes/{class_id}", response_model=schemas.ClassRead)
def get_class_detail(class_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin chi tiết của một lớp học"""
    class_obj = crud.get_class(db, class_id)
    
    if not class_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")
    
    return class_obj


@router.get("/students/{student_id}/grades", response_model=list[schemas.GradeRead])
def get_student_grades_api(
    student_id: int,
    class_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Lấy điểm của sinh viên, có thể lọc theo lớp
    
    Query params:
    - class_id: (Optional) Lọc điểm theo lớp học
    """
    grades = crud.get_student_grades(db, student_id, class_id)
    return grades

@router.get("/students/{student_id}/enrollments", response_model=list[schemas.EnrollmentRead])
def get_student_enrollments_api(student_id: int, db: Session = Depends(get_db)):
    """Lấy danh sách các lớp học mà sinh viên đã đăng ký"""
    enrollments = crud.get_student_enrollments(db, student_id)
    return enrollments