from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import teacher_crud, teacher_schemas, database, models
from .jwt_auth import get_current_user, get_db

router = APIRouter(prefix="/teacher", tags=["teacher"])



@router.get("/classes", response_model=List[teacher_schemas.ClassResponse])
async def get_teacher_classes(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Access denied")
    return teacher_crud.get_teacher_classes(db, current_user.id)



@router.get("/students/{class_id}", response_model=List[teacher_schemas.StudentInClass])
async def get_students_in_class(
        class_id: int,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Access denied")
    return teacher_crud.get_students_by_class(db, class_id, current_user.id)


@router.put("/grade/{student_id}/{class_id}")
async def update_student_grade(
        student_id: int,
        class_id: int,
        grade_data: teacher_schemas.GradeUpdate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Access denied")

    result = teacher_crud.update_grade(db, student_id, class_id, grade_data.grade)
    if not result:
        raise HTTPException(status_code=404, detail="Student not found")

    return {"message": "Grade updated successfully"}


@router.get("/schedule")
async def get_teacher_schedule(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Access denied")
    return teacher_crud.get_teacher_schedule(db, current_user.id)


@router.get("/profile")
async def get_teacher_profile(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Access denied")
    return teacher_crud.get_teacher_profile(db, current_user.id)
