from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db import schemas, models, crud, database
from . import jwt_auth

router = APIRouter(
    prefix="/student",
    tags=["Student"]
)

# ✅ Lấy danh sách lớp học của sinh viên (Enrollments)
@router.get("/{student_id}/enrollments")
def get_student_enrollments(
    student_id: int,
    db: Session = Depends(database.get_db),
    user: dict = Depends(jwt_auth.auth)
):
    """Lấy danh sách các lớp học mà sinh viên đã đăng ký"""
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student_id
    ).all()
    
    result = []
    for enrollment in enrollments:
        result.append({
            "student_id": enrollment.student_id,
            "class_id": enrollment.class_id,
            "enroll_date": str(enrollment.enroll_date) if enrollment.enroll_date else None
        })
    
    return result


# ✅ Lấy thông tin chi tiết lớp học
@router.get("/classes/{class_id}")
def get_class_info(
    class_id: int,
    db: Session = Depends(database.get_db),
    user: dict = Depends(jwt_auth.auth)
):
    """Lấy thông tin chi tiết của một lớp học"""
    class_info = db.query(models.Class).filter(
        models.Class.class_id == class_id
    ).first()
    
    if not class_info:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")
    
    return {
        "class_id": class_info.class_id,
        "class_name": class_info.class_name,
        "year": class_info.year,
        "semester": class_info.semester
    }


# ✅ Lấy điểm của sinh viên theo lớp học
@router.get("/{student_id}/grades")
def get_student_grades(
    student_id: int,
    class_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    user: dict = Depends(jwt_auth.auth)
):
    """Lấy điểm của sinh viên
    - Nếu có class_id: lấy điểm của lớp đó
    - Nếu không có class_id: lấy tất cả điểm
    """
    query = db.query(models.Grade).filter(
        models.Grade.student_id == student_id
    )
    
    if class_id:
        query = query.filter(models.Grade.class_id == class_id)
    
    grades = query.all()
    
    result = []
    for grade in grades:
        result.append({
            "grade_id": grade.grade_id,
            "student_id": grade.student_id,
            "class_id": grade.class_id,
            "subject": grade.subject,
            "score": float(grade.score),
            "updated_at": str(grade.updated_at) if grade.updated_at else None
        })
    
    return result


# ✅ Lấy thống kê điểm của sinh viên
@router.get("/{student_id}/statistics")
def get_student_statistics(
    student_id: int,
    db: Session = Depends(database.get_db),
    user: dict = Depends(jwt_auth.auth)
):
    """Lấy thống kê điểm của sinh viên"""
    grades = db.query(models.Grade).filter(
        models.Grade.student_id == student_id
    ).all()
    
    if not grades:
        return {
            "total_subjects": 0,
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0
        }
    
    scores = [float(g.score) for g in grades]
    
    return {
        "total_subjects": len(scores),
        "average_score": round(sum(scores) / len(scores), 2),
        "highest_score": max(scores),
        "lowest_score": min(scores)
    }


# ✅ Lấy tất cả lớp học (dành cho admin/teacher)
@router.get("/classes")
def get_all_classes(
    db: Session = Depends(database.get_db),
    user: dict = Depends(jwt_auth.auth)
):
    """Lấy danh sách tất cả lớp học"""
    classes = db.query(models.Class).all()
    
    result = []
    for cls in classes:
        result.append({
            "class_id": cls.class_id,
            "class_name": cls.class_name,
            "year": cls.year,
            "semester": cls.semester
        })
    
    return result


# ===== OLD ROUTES (giữ lại để tương thích) =====
@router.get("/test")
def test_student():
    return {"message": "Student router connected!"}


@router.get("/all")
def get_all_students(db: Session = Depends(database.get_db)):
    students = db.query(models.Student).all()
    return students


@router.get("/{student_id}")
def get_student_by_id(student_id: int, db: Session = Depends(database.get_db)):
    student = db.query(models.Student).filter(models.Student.student_id == student_id).first()
    if not student:
        return {"error": "Student not found"}
    return student


# ✅ Thêm sinh viên mới
@router.post("/add")
def add_student(student: schemas.StudentCreate, db: Session = Depends(database.get_db)):
    new_student = models.Student(
        username=student.username,
        password=student.password,
        full_name=student.full_name,
        email=student.email,
        student_code=student.student_code,
        birthdate=student.birthdate
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {"message": "Student added successfully!", "student": new_student}
