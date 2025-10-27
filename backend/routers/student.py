from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import schemas, models, crud, database

router = APIRouter(
    prefix="/student",
    tags=["Student"]
)

@router.get("/test")
def test_student():
    return {"message": "Student router connected!"}


@router.get("/all")
def get_all_students(db: Session = Depends(database.get_db)):
    students = db.query(models.Student).all()
    return students


@router.get("/{student_id}")
def get_student_by_id(student_id: int, db: Session = Depends(database.get_db)):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return {"error": "Student not found"}
    return student


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

