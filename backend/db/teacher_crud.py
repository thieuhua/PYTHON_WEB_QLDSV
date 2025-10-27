# backend/db/teacher_crud.py
from typing import List, Dict, Optional, Tuple
import secrets
from sqlalchemy.orm import Session
from sqlalchemy import and_

from . import models, schemas, crud  # assumes crud.get_user_by_username and crud.create_user exist
from .database import SessionLocal

# --- Helper ---
def _ensure_student_profile(db: Session, user):
    """Ensure a Student row exists for a User; return Student model."""
    student = db.query(models.Student).filter(models.Student.student_id == user.user_id).first()
    if not student:
        student = models.Student(student_id=user.user_id, student_code=getattr(user, 'student_code', None))
        db.add(student)
        db.commit()
        db.refresh(student)
    return student

# --- Get classes that a teacher is assigned to ---
def get_teacher_classes(db: Session, teacher_id: int) -> List[models.Class]:
    """
    Return list of Class models assigned to teacher_id via TeachingAssignment.
    """
    classes = (
        db.query(models.Class)
        .join(models.TeachingAssignment, models.Class.class_id == models.TeachingAssignment.class_id)
        .filter(models.TeachingAssignment.teacher_id == teacher_id)
        .all()
    )
    return classes

# --- Create a class and assign to teacher ---
def create_class_for_teacher(db: Session, teacher_id: int, class_in: schemas.ClassCreate) -> models.Class:
    new_class = models.Class(
        class_name=class_in.class_name,
        year=class_in.year,
        semester=class_in.semester
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    # create teaching assignment
    ta = models.TeachingAssignment(teacher_id=teacher_id, class_id=new_class.class_id)
    db.add(ta)
    db.commit()
    return new_class

# --- Get detailed class info: class + enrolled students + grades ---
def get_class_detail(db: Session, class_id: int) -> Optional[Dict]:
    cls = db.query(models.Class).filter(models.Class.class_id == class_id).first()
    if not cls:
        return None

    # students via enrollments
    enroll_rows = (
        db.query(models.Enrollment, models.Student, models.User)
        .join(models.Student, models.Enrollment.student_id == models.Student.student_id)
        .join(models.User, models.User.user_id == models.Student.student_id)
        .filter(models.Enrollment.class_id == class_id)
        .all()
    )

    # fetch all grades for this class
    grade_rows = db.query(models.Grade).filter(models.Grade.class_id == class_id).all()
    # build mapping (student_id -> { subject: score, ... })
    grade_map = {}
    for g in grade_rows:
        grade_map.setdefault(g.student_id, {})[g.subject] = g.score

    students = []
    for enroll, student, user in enroll_rows:
        g = grade_map.get(student.student_id, {})
        students.append({
            "student_id": student.student_id,
            "full_name": user.full_name or user.username,
            "student_code": student.student_code,
            # Map to the three fields expected by the frontend (attendance, mid, final).
            # If you support arbitrary subjects later, adapt frontend or return list form.
            "grades": {
                "attendance": g.get("attendance", "") if g.get("attendance", None) is not None else "",
                "mid": g.get("mid", "") if g.get("mid", None) is not None else "",
                "final": g.get("final", "") if g.get("final", None) is not None else ""
            }
        })

    result = {
        "class_id": cls.class_id,
        "class_name": cls.class_name,
        "year": cls.year,
        "semester": cls.semester,
        # optional: expose max_students or other metadata; if not in model you can set None
        "max_students": getattr(cls, "max_students", None),
        "students": students
    }
    return result

# --- Add (or create) a student and enroll into class ---
def add_student_to_class(db: Session, class_id: int, full_name: str, student_code: str) -> Dict:
    """
    If user with username==student_code exists -> ensure Student profile and Enrollment.
    Else create a new User (student) and Student profile, then Enrollment.
    Returns a dict with minimal student info.
    """
    # Try find user by username (we assume username = student_code)
    user = crud.get_user_by_username(db, student_code)
    if not user:
        # create user with random password; crud.create_user should handle student_profile fields if supported
        temp_pass = secrets.token_urlsafe(8)
        uc = schemas.UserCreate(
            username=student_code,
            password=temp_pass,
            full_name=full_name,
            email=None,
            role=schemas.UserRole.student,
            student_code=student_code
        )
        user = crud.create_user(db, uc)

    # ensure student profile exists
    student = db.query(models.Student).filter(models.Student.student_id == user.user_id).first()
    if not student:
        student = models.Student(student_id=user.user_id, student_code=student_code)
        db.add(student)
        db.commit()
        db.refresh(student)

    # ensure enrollment
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.class_id == class_id,
        models.Enrollment.student_id == student.student_id
    ).first()
    if not enrollment:
        enrollment = models.Enrollment(student_id=student.student_id, class_id=class_id)
        db.add(enrollment)
        db.commit()

    return {
        "student_id": student.student_id,
        "full_name": user.full_name or user.username,
        "student_code": student.student_code
    }

# --- Remove (unenroll) a student from class ---
def remove_student_from_class(db: Session, class_id: int, student_id: int) -> bool:
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.class_id == class_id,
        models.Enrollment.student_id == student_id
    ).first()
    if not enrollment:
        return False
    db.delete(enrollment)
    db.commit()
    return True

# --- Save or update grades for a class ---
def save_grades(db: Session, class_id: int, grades: List[Dict]) -> None:
    """
    grades: list of { student_id, subject, score }
    Subject expected: "attendance", "mid", "final" (matching frontend).
    """
    for g in grades:
        student_id = int(g["student_id"])
        subject = str(g["subject"])
        score = float(g["score"])

        existing = db.query(models.Grade).filter(
            models.Grade.class_id == class_id,
            models.Grade.student_id == student_id,
            models.Grade.subject == subject
        ).first()
        if existing:
            existing.score = score
        else:
            newg = models.Grade(student_id=student_id, class_id=class_id, subject=subject, score=score)
            db.add(newg)
    db.commit()
