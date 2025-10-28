from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db import schemas, models, crud, database
from . import jwt_auth

router = APIRouter(
    prefix="/student",
    tags=["Student"]
)

# ✅ CHỈ GIỮ CÁC ROUTES KHÔNG BỊ CONFLICT VỚI API.PY

@router.get("/test")
def test_student():
    return {"message": "Student router connected!"}


@router.get("/all")
def get_all_students(
    db: Session = Depends(database.get_db),
    user: dict = Depends(jwt_auth.auth)
):
    """Lấy danh sách tất cả sinh viên (admin only)"""
    students = db.query(models.Student).all()
    return students


@router.get("/{student_id}/profile")
def get_student_profile(
    student_id: int, 
    db: Session = Depends(database.get_db),
    user: dict = Depends(jwt_auth.auth)
):
    """Lấy thông tin profile đầy đủ của sinh viên"""
    student = db.query(models.Student).filter(
        models.Student.student_id == student_id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Join với User để lấy thêm thông tin
    user_info = db.query(models.User).filter(
        models.User.user_id == student_id
    ).first()
    
    return {
        "student_id": student.student_id,
        "student_code": student.student_code,
        "birthdate": str(student.birthdate) if student.birthdate else None,
        "full_name": user_info.full_name if user_info else None,
        "email": user_info.email if user_info else None
    }


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


@router.post("/add")
def add_student(
    student: schemas.StudentCreate, 
    db: Session = Depends(database.get_db),
    user: dict = Depends(jwt_auth.auth)
):
    """Thêm sinh viên mới (admin/teacher only)"""
    try:
        new_student = crud.create_student(db, student)
        return {"message": "Student added successfully!", "student_id": new_student.student_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))