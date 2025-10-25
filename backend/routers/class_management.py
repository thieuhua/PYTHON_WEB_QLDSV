from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db import teacher_crud, teacher_schemas
from ..db.database import get_db
from . import jwt_auth

router = APIRouter(prefix="/api/teacher")

# Middleware để kiểm tra role teacher
async def verify_teacher(
    token_data: dict = Depends(jwt_auth.auth),
    db: Session = Depends(get_db)
):
    if 'id' not in token_data:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    
    teacher = teacher_crud.get_teacher(db, token_data['id'])
    if not teacher:
        raise HTTPException(status_code=403, detail="Chỉ giáo viên mới có quyền truy cập")
    return teacher

@router.get("/classes", response_model=List[teacher_schemas.TeacherClassWithStats])
async def get_teacher_classes(
    teacher = Depends(verify_teacher),
    db: Session = Depends(get_db)
):
    """Lấy danh sách lớp học của giáo viên"""
    return teacher_crud.get_teacher_classes(db, teacher.teacher_id)

@router.post("/classes", response_model=teacher_schemas.TeacherClassWithStats)
async def create_class(
    class_data: teacher_schemas.TeacherClassCreate,
    teacher = Depends(verify_teacher),
    db: Session = Depends(get_db)
):
    """Tạo lớp học mới"""
    return teacher_crud.create_class(db, teacher.teacher_id, class_data)

@router.get("/classes/{class_id}", response_model=teacher_schemas.ClassDetails)
async def get_class_details(
    class_id: int,
    teacher = Depends(verify_teacher),
    db: Session = Depends(get_db)
):
    """Lấy chi tiết lớp học và danh sách sinh viên"""
    return teacher_crud.get_class_details(db, class_id, teacher.teacher_id)

@router.put("/classes/{class_id}", response_model=teacher_schemas.TeacherClassWithStats)
async def update_class(
    class_id: int,
    update_data: teacher_schemas.TeacherClassUpdate,
    teacher = Depends(verify_teacher),
    db: Session = Depends(get_db)
):
    """Cập nhật thông tin lớp học"""
    return teacher_crud.update_class(db, class_id, teacher.teacher_id, update_data)

@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: int,
    teacher = Depends(verify_teacher),
    db: Session = Depends(get_db)
):
    """Xóa lớp học (chỉ khi chưa có sinh viên)"""
    teacher_crud.delete_class(db, class_id, teacher.teacher_id)
    return {"message": "Đã xóa lớp học"}

@router.post("/classes/{class_id}/students")
async def add_student(
    class_id: int,
    student_data: teacher_schemas.StudentEnrollment,
    teacher = Depends(verify_teacher),
    db: Session = Depends(get_db)
):
    """Thêm sinh viên vào lớp"""
    student = teacher_crud.add_student_to_class(
        db, class_id, teacher.teacher_id, student_data
    )
    return {"message": "Đã thêm sinh viên vào lớp", "student_id": student.student_id}

@router.delete("/classes/{class_id}/students/{student_id}")
async def remove_student(
    class_id: int,
    student_id: int,
    teacher = Depends(verify_teacher),
    db: Session = Depends(get_db)
):
    """Xóa sinh viên khỏi lớp"""
    teacher_crud.remove_student_from_class(db, class_id, teacher.teacher_id, student_id)
    return {"message": "Đã xóa sinh viên khỏi lớp"}

@router.put("/classes/{class_id}/students/{student_id}/grades")
async def update_grades(
    class_id: int,
    student_id: int,
    grades: teacher_schemas.GradeUpdate,
    teacher = Depends(verify_teacher),
    db: Session = Depends(get_db)
):
    """Cập nhật điểm cho sinh viên"""
    updated = teacher_crud.update_student_grades(
        db, class_id, teacher.teacher_id, student_id, grades
    )
    return {"message": "Đã cập nhật điểm", "grade_id": updated.grade_id}
