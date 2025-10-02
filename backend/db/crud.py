from sqlalchemy.orm import Session
from datetime import date

from ..routers import schemas
from . import models

def get_items(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        username=user.username,
        password=user.password,
        role=user.role,
        name=user.name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, update_data: dict):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user


# =======================
# CRUD cho Course
# =======================
def create_course(db: Session, course: schemas.CourseCreate):
    db_course = models.Course(
        teacherId=course.teacherId,
        courseName=course.courseName
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def get_course(db: Session, course_id: int):
    return db.query(models.Course).filter(models.Course.courseId == course_id).first()

def get_courses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Course).offset(skip).limit(limit).all()

def update_course(db: Session, course_id: int, update_data: dict):
    course = db.query(models.Course).filter(models.Course.courseId == course_id).first()
    if not course:
        return None
    for key, value in update_data.items():
        setattr(course, key, value)
    db.commit()
    db.refresh(course)
    return course

def delete_course(db: Session, course_id: int):
    course = db.query(models.Course).filter(models.Course.courseId == course_id).first()
    if not course:
        return None
    db.delete(course)
    db.commit()
    return course


# =======================
# CRUD cho Student
# =======================
def enroll_student(db: Session, student: schemas.StudentCreate):
    db_student = models.Student(
        studentId=student.studentId,
        courseId=student.courseId
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def get_students_by_course(db: Session, course_id: int):
    return db.query(models.Student).filter(models.Student.courseId == course_id).all()

def get_student(db: Session, student_id: int):
    return db.query(models.Student).filter(models.Student.id == student_id).first()

def remove_student(db: Session, student_id: int):
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        return None
    db.delete(student)
    db.commit()
    return student


# =======================
# CRUD cho Baithi
# =======================
def create_baithi(db: Session, baithi: schemas.BaithiCreate):
    db_bt = models.Baithi(
        tenBaiThi=baithi.tenBaiThi,
        courseId=baithi.courseId
    )
    db.add(db_bt)
    db.commit()
    db.refresh(db_bt)
    return db_bt

def get_baithi_by_course(db: Session, course_id: int):
    return db.query(models.Baithi).filter(models.Baithi.courseId == course_id).all()

def get_baithi(db: Session, idBaithi: int):
    return db.query(models.Baithi).filter(models.Baithi.idBaithi == idBaithi).first()

def delete_baithi(db: Session, idBaithi: int):
    bt = db.query(models.Baithi).filter(models.Baithi.idBaithi == idBaithi).first()
    if not bt:
        return None
    db.delete(bt)
    db.commit()
    return bt


# =======================
# CRUD cho DiemThi
# =======================
def create_diemthi(db: Session, diem: schemas.DiemThiCreate):
    db_diem = models.DiemThi(
        idBaithi=diem.idBaithi,
        studentId=diem.studentId,
        date=diem.date or date.today(),
        grade=diem.grade
    )
    db.add(db_diem)
    db.commit()
    db.refresh(db_diem)
    return db_diem

def get_diemthi_by_student(db: Session, student_id: int):
    return db.query(models.DiemThi).filter(models.DiemThi.studentId == student_id).all()

def get_diemthi_by_baithi(db: Session, idBaithi: int):
    return db.query(models.DiemThi).filter(models.DiemThi.idBaithi == idBaithi).all()

def update_diemthi(db: Session, diem_id: int, update_data: dict):
    diem = db.query(models.DiemThi).filter(models.DiemThi.id == diem_id).first()
    if not diem:
        return None
    for key, value in update_data.items():
        setattr(diem, key, value)
    db.commit()
    db.refresh(diem)
    return diem

def delete_diemthi(db: Session, diem_id: int):
    diem = db.query(models.DiemThi).filter(models.DiemThi.id == diem_id).first()
    if not diem:
        return None
    db.delete(diem)
    db.commit()
    return diem
