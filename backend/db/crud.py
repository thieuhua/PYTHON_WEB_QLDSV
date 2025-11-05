from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, schemas
from typing import List, Optional
from datetime import date

# ==============================================================
# USER CRUD
# ==============================================================

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(
        username=user.username,
        password=user.password,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
    )
    db.add(db_user)
    db.flush()

    # Tạo profile tương ứng với role
    if user.role == models.UserRole.student and hasattr(user, 'student_code'):
        student = models.Student(
            student_id=db_user.user_id,
            student_code=user.student_code,
            birthdate=user.birthdate if hasattr(user, 'birthdate') else None
        )
        db.add(student)
    
    elif user.role == models.UserRole.teacher:
        teacher = models.Teacher(
            teacher_id=db_user.user_id,
            department=user.department if hasattr(user, 'department') else None,
            title=user.title if hasattr(user, 'title') else None
        )
        db.add(teacher)

    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> None:
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()


# ==============================================================
# TEACHER CRUD
# ==============================================================

def create_teacher(db: Session, teacher: schemas.TeacherCreate) -> models.Teacher:
    db_teacher = models.Teacher(
        teacher_id=teacher.user_id,
        department=teacher.department,
        title=teacher.title,
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


def get_teacher(db: Session, teacher_id: int) -> Optional[models.Teacher]:
    return db.query(models.Teacher).filter(models.Teacher.teacher_id == teacher_id).first()


def get_teachers(db: Session) -> List[models.Teacher]:
    return db.query(models.Teacher).all()


# ==============================================================
# STUDENT CRUD
# ==============================================================

def create_student(db: Session, student: schemas.StudentCreate) -> models.Student:
    db_student = models.Student(
        student_id=student.user_id,
        student_code=student.student_code,
        birthdate=student.birthdate,
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def get_student(db: Session, student_id: int) -> Optional[models.Student]:
    return db.query(models.Student).filter(models.Student.student_id == student_id).first()


def get_students(db: Session) -> List[models.Student]:
    return db.query(models.Student).all()


# ==============================================================
# CLASS CRUD
# ==============================================================

def create_class(db: Session, class_: schemas.ClassCreate) -> models.Class:
    db_class = models.Class(
        class_name=class_.class_name,
        year=class_.year,
        semester=class_.semester,
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class


def get_class(db: Session, class_id: int) -> Optional[models.Class]:
    return db.query(models.Class).filter(models.Class.class_id == class_id).first()


def get_classes(db: Session) -> List[models.Class]:
    return db.query(models.Class).all()


# ==============================================================
# ENROLLMENT (Student-Class) - FIXED
# ==============================================================

def enroll_student(db: Session, enrollment: schemas.EnrollmentCreate) -> models.Enrollment:
    db_enroll = models.Enrollment(
        student_id=enrollment.student_id,
        class_id=enrollment.class_id,
        enroll_date=date.today()
    )
    db.add(db_enroll)
    db.commit()
    db.refresh(db_enroll)
    return db_enroll


def get_enrollments(db: Session) -> List[models.Enrollment]:
    return db.query(models.Enrollment).all()


# ✅ THÊM HÀM NÀY - Lấy enrollments theo student_id
def get_student_enrollments(db: Session, student_id: int) -> List[models.Enrollment]:
    """Lấy danh sách lớp học mà sinh viên đã đăng ký"""
    return db.query(models.Enrollment).filter(
        models.Enrollment.student_id == student_id
    ).all()


# ==============================================================
# TEACHING ASSIGNMENT (Teacher-Class)
# ==============================================================

def assign_teacher(db: Session, assign: schemas.TeachingAssignmentCreate) -> models.TeachingAssignment:
    db_assign = models.TeachingAssignment(
        teacher_id=assign.teacher_id,
        class_id=assign.class_id,
        assigned_date=date.today()
    )
    db.add(db_assign)
    db.commit()
    db.refresh(db_assign)
    return db_assign


def get_assignments(db: Session) -> List[models.TeachingAssignment]:
    return db.query(models.TeachingAssignment).all()


# ==============================================================
# GRADE CRUD - FIXED
# ==============================================================

def create_grade(db: Session, grade: schemas.GradeCreate) -> models.Grade:
    db_grade = models.Grade(
        student_id=grade.student_id,
        class_id=grade.class_id,
        subject=grade.subject,
        score=grade.score,
    )
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade


def update_grade(db: Session, grade_id: int, data: schemas.GradeUpdate) -> models.Grade:
    db_grade = db.query(models.Grade).filter(models.Grade.grade_id == grade_id).first()
    if not db_grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(db_grade, key, value)

    db.commit()
    db.refresh(db_grade)
    return db_grade


def get_grades_by_student(db: Session, student_id: int) -> List[models.Grade]:
    return db.query(models.Grade).filter(models.Grade.student_id == student_id).all()


def get_grades_by_class(db: Session, class_id: int) -> List[models.Grade]:
    return db.query(models.Grade).filter(models.Grade.class_id == class_id).all()


# ✅ THÊM HÀM NÀY - Lấy grades có thể filter theo class
def get_student_grades(db: Session, student_id: int, class_id: Optional[int] = None) -> List[models.Grade]:
    """Lấy điểm của sinh viên, có thể filter theo class_id"""
    query = db.query(models.Grade).filter(models.Grade.student_id == student_id)
    
    if class_id is not None:
        query = query.filter(models.Grade.class_id == class_id)
    
    return query.all()

def get_student_grades_by_subject(db: Session, student_id: int) -> dict[str, list[float]]:
    """
    Lấy tất cả điểm của một sinh viên, nhóm theo môn.
    Trả về dict: { subject_name: [scores...] }
    """
    grades = db.query(models.Grade).filter(models.Grade.student_id == student_id).all()
    subject_scores: dict[str, list[float]] = {}

    for g in grades:
        if g.subject not in subject_scores:
            subject_scores[g.subject] = []
        subject_scores[g.subject].append(g.score)

    return subject_scores
