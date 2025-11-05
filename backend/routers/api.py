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
    try:
        # Kiểm tra username đã tồn tại chưa
        existing_user = crud.get_user_by_username(db, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username đã tồn tại")

        # Tạo user object
        hashedpassw: str = jwt_auth.hash_password(user.password)
        db_user = models.User(
            username=user.username,
            password=hashedpassw,
            full_name="NoName",
            email=None,
            role=models.UserRole.student
        )
        db.add(db_user)
        db.flush()  # Lấy user_id nhưng chưa commit

        # Tạo student profile với mã tự động
        student_code = f"ST{db_user.user_id:04d}"
        db_student = models.Student(
            student_id=db_user.user_id,
            student_code=student_code,
            birthdate=None
        )
        db.add(db_student)

        # Commit cả user và student cùng lúc
        db.commit()
        db.refresh(db_user)

        print(f"✅ Đã tạo user '{user.username}' và student profile với mã: {student_code}")

        token = jwt_auth.create_token({"username": db_user.username, "password": db_user.password, "role": db_user.role.value})

        return {
            "token": token,
            "message": "Đăng ký thành công",
            "username": user.username
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print("❌ Lỗi khi tạo user:", str(e))
        import traceback
        traceback.print_exc()

        # Kiểm tra lỗi duplicate
        error_msg = str(e).lower()
        if 'unique' in error_msg or 'duplicate' in error_msg:
            raise HTTPException(status_code=400, detail="Username hoặc mã sinh viên đã tồn tại")

        raise HTTPException(status_code=400, detail=f"Lỗi đăng ký: {str(e)}")


@router.post("/login")
def login(user: UserAuth, db: Session = Depends(get_db)):
    print("user:", user.username, user.password)
    user_db = crud.get_user_by_username(db, user.username)

    ok = jwt_auth.verify_password(user.password, user_db.password)

    if not ok:
        raise HTTPException(401)

    token = jwt_auth.create_token({"username": user_db.username, "id": user_db.user_id, "role": user_db.role.value})
    print("Generated token:", token)

    return {
        "token": token,
        "message": "Đăng nhập thành công",
        "username": user.username
    }


@router.get("/me", response_model=schemas.MeRead)
def getMe(user: dict = Depends(jwt_auth.auth), db: Session = Depends(get_db)):
    """Return current authenticated user with related profiles (student_profile / teacher_profile)."""
    db_user = crud.get_user_by_username(db, user.get('username'))
    if not db_user:
        raise HTTPException(404, detail="User not found")
    return db_user


@router.put("/me", response_model=schemas.MeRead)
def update_me(update: schemas.UserUpdate, user: dict = Depends(jwt_auth.auth), db: Session = Depends(get_db)):
    """Update current user's profile and related student/teacher records."""
    db_user = crud.get_user_by_username(db, user.get('username'))
    if not db_user:
        raise HTTPException(404, detail="User not found")

    data = update.model_dump(exclude_unset=True)

    if 'password' in data and data['password']:
        db_user.password = jwt_auth.hash_password(data.pop('password'))

    for field in ['full_name', 'email', 'role']:
        if field in data:
            setattr(db_user, field, data.pop(field))

    effective_role = getattr(db_user.role, 'value', db_user.role) if hasattr(db_user.role, 'value') else db_user.role
    if 'role' in update.__fields_set__:
        effective_role = update.role.value if hasattr(update.role, 'value') else update.role

    if str(effective_role) == 'student':
        student = crud.get_student(db, db_user.user_id)
        if student:
            # [SỬA] Cho phép update student_code và birthdate khi student đã tồn tại
            if 'student_code' in data:
                new_code = data.pop('student_code')
                # Kiểm tra mã không được rỗng
                if new_code and new_code.strip():
                    new_code = new_code.strip()
                    # Kiểm tra xem mã mới có trùng với mã khác không (trừ mã hiện tại)
                    existing = db.query(models.Student).filter(
                        models.Student.student_code == new_code,
                        models.Student.student_id != student.student_id
                    ).first()
                    if existing:
                        raise HTTPException(status_code=400, detail=f"Mã sinh viên '{new_code}' đã tồn tại")
                    student.student_code = new_code
                elif new_code == '' or new_code is None:
                    # Nếu gửi chuỗi rỗng hoặc None, không update (giữ nguyên mã cũ)
                    pass
            if 'birthdate' in data:
                student.birthdate = data.pop('birthdate')
        else:
            student_code = data.pop('student_code', None) if 'student_code' in data else None
            if not student_code:
                student_code = f"ST{db_user.user_id:04d}"
            sc = schemas.StudentCreate(user_id=db_user.user_id, student_code=student_code,
                                       birthdate=data.pop('birthdate', None))
            try:
                crud.create_student(db, sc)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to create student profile: {e}")

    if str(effective_role) == 'teacher':
        teacher = crud.get_teacher(db, db_user.user_id)
        if teacher:
            if 'department' in data:
                teacher.department = data.pop('department')
            if 'title' in data:
                teacher.title = data.pop('title')
        else:
            tc = schemas.TeacherCreate(user_id=db_user.user_id, department=data.pop('department', None),
                                       title=data.pop('title', None))
            try:
                crud.create_teacher(db, tc)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to create teacher profile: {e}")

    try:
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        # Kiểm tra nếu là lỗi duplicate key
        error_msg = str(e).lower()
        if 'unique' in error_msg or 'duplicate' in error_msg:
            raise HTTPException(status_code=400, detail="Mã sinh viên hoặc email đã tồn tại")
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật: {str(e)}")

    return db_user


class UpdateRoleRequest(BaseModel):
    username: str
    new_role: str


@router.post("/admin/update-role")
def update_user_role(
    role_data: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(jwt_auth.auth)  # 👈 Bắt buộc có token hợp lệ
):
    # ✅ Kiểm tra nếu không phải admin thì chặn
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied. Admin only.")

    db_user = crud.get_user_by_username(db, role_data.username)
    if not db_user:
        raise HTTPException(404, detail="User not found")

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


# ✅ CÁC API CHO STUDENT - CHỈ GIỮ MỘT BẢN DUY NHẤT
@router.get("/students/{student_id}/enrollments", response_model=list[schemas.EnrollmentRead])
def get_student_enrollments_api(
        student_id: int,
        db: Session = Depends(get_db),
        user: dict = Depends(jwt_auth.auth)
):
    """Lấy danh sách các lớp học mà sinh viên đã đăng ký"""
    enrollments = crud.get_student_enrollments(db, student_id)
    return enrollments


@router.get("/classes/{class_id}", response_model=schemas.ClassRead)
def get_class_detail(
        class_id: int,
        db: Session = Depends(get_db),
        user: dict = Depends(jwt_auth.auth)
):
    """Lấy thông tin chi tiết của một lớp học"""
    class_obj = crud.get_class(db, class_id)

    if not class_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")

    return class_obj


@router.get("/students/{student_id}/grades", response_model=list[schemas.GradeRead])
def get_student_grades_api(
        student_id: int,
        class_id: int = None,
        db: Session = Depends(get_db),
        user: dict = Depends(jwt_auth.auth)
):
    """
    Lấy điểm của sinh viên, có thể lọc theo lớp

    Query params:
    - class_id: (Optional) Lọc điểm theo lớp học
    """
    grades = crud.get_student_grades(db, student_id, class_id)
    return grades