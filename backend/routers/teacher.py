# backend/routers/teacher.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from sqlalchemy.orm import Session

from ..db import teacher_crud, crud, database, schemas, models
from ..db.database import get_db
from ..routers import jwt_auth
router = APIRouter(
    prefix="/teacher",
    tags=["Teacher"]
)

# --- Dependency: get current teacher user from Authorization header (Bearer <token>) ---
def get_current_teacher(request: Request, db: Session = Depends(get_db)):
    # tries cookie first then Authorization header similar to main.get_current_user
    token = None
    token = request.cookies.get("token")
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.split("Bearer ")[1]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = jwt_auth.decode_tokenNE(token)
        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    db_user = crud.get_user_by_username(db, username)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if db_user.role != schemas.UserRole.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires teacher role")
    return db_user

# --- Routes ---

@router.get("/classes", summary="Get classes for current teacher")
def list_classes(current_user: models.User = Depends(get_current_teacher), db: Session = Depends(get_db)):
    teacher_id = current_user.user_id
    cls = teacher_crud.get_teacher_classes(db, teacher_id)
    # simple serialization
    return [
        {
            "class_id": c.class_id,
            "class_name": c.class_name,
            "year": c.year,
            "semester": c.semester,
            # optional fields
        } for c in cls
    ]

@router.post("/classes", summary="Create class and assign to current teacher")
def create_class(class_in: schemas.ClassCreate, current_user: models.User = Depends(get_current_teacher), db: Session = Depends(get_db)):
    teacher_id = current_user.user_id
    newc = teacher_crud.create_class_for_teacher(db, teacher_id, class_in)
    return {"class_id": newc.class_id}

@router.get("/classes/{class_id}", summary="Get class detail (students + grades)")
def get_class(class_id: int, current_user: models.User = Depends(get_current_teacher), db: Session = Depends(get_db)):
    # optional: verify teacher has assignment to this class
    # check assignment
    ta = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_id == class_id,
        models.TeachingAssignment.teacher_id == current_user.user_id
    ).first()
    if not ta:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")

    detail = teacher_crud.get_class_detail(db, class_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Class not found")
    return detail

@router.post("/classes/{class_id}/students", summary="Add (or create) student and enroll into class")
def add_student(class_id: int, payload: dict, current_user: models.User = Depends(get_current_teacher), db: Session = Depends(get_db)):
    # simple payload validation
    full_name = payload.get("full_name")
    student_code = payload.get("student_code")
    if not student_code or not full_name:
        raise HTTPException(status_code=400, detail="full_name and student_code required")
    # ensure teacher assigned to class
    ta = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_id == class_id,
        models.TeachingAssignment.teacher_id == current_user.user_id
    ).first()
    if not ta:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")

    info = teacher_crud.add_student_to_class(db, class_id, full_name, student_code)
    return info

@router.delete("/classes/{class_id}/students/{student_id}", summary="Unenroll student from a class")
def delete_student(class_id: int, student_id: int, current_user: models.User = Depends(get_current_teacher), db: Session = Depends(get_db)):
    ta = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_id == class_id,
        models.TeachingAssignment.teacher_id == current_user.user_id
    ).first()
    if not ta:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")

    ok = teacher_crud.remove_student_from_class(db, class_id, student_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return {"ok": True}

@router.post("/classes/{class_id}/grades", summary="Save/update grades (bulk)")
def save_grades(class_id: int, grades: List[schemas.GradeCreate], current_user: models.User = Depends(get_current_teacher), db: Session = Depends(get_db)):
    # verify teacher assigned to class
    ta = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_id == class_id,
        models.TeachingAssignment.teacher_id == current_user.user_id
    ).first()
    if not ta:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")

    # call crud to save
    # convert Pydantic objects to dicts
    payload = [g.model_dump() for g in grades]
    teacher_crud.save_grades(db, class_id, payload)
    return {"ok": True}
