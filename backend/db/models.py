from sqlalchemy import (
    Column, Integer, String, Date, ForeignKey, Enum, Float, DateTime, func
)
from sqlalchemy.orm import relationship
from .database import Base
import enum

# -------- ENUM ROLE --------
class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"

# -------- USER --------
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)  # hashed
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.student)

    # Relationships
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)
    student_profile = relationship("Student", back_populates="user", uselist=False)

# -------- TEACHER --------
class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    department = Column(String)
    title = Column(String)

    user = relationship("User", back_populates="teacher_profile")
    assignments = relationship("TeachingAssignment", back_populates="teacher")

# -------- STUDENT --------
class Student(Base):
    __tablename__ = "students"

    student_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    student_code = Column(String, unique=True)
    birthdate = Column(Date)

    user = relationship("User", back_populates="student_profile")
    enrollments = relationship("Enrollment", back_populates="student")
    grades = relationship("Grade", back_populates="student")

# -------- CLASS --------
class Class(Base):
    __tablename__ = "classes"

    class_id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)

    enrollments = relationship("Enrollment", back_populates="class_")
    teaching_assignments = relationship("TeachingAssignment", back_populates="class_")
    grades = relationship("Grade", back_populates="class_")

# -------- ENROLLMENT (Học sinh - lớp) --------
class Enrollment(Base):
    __tablename__ = "enrollments"

    student_id = Column(Integer, ForeignKey("students.student_id"), primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.class_id"), primary_key=True)
    enroll_date = Column(Date, server_default=func.current_date())

    student = relationship("Student", back_populates="enrollments")
    class_ = relationship("Class", back_populates="enrollments")

# -------- TEACHING ASSIGNMENT (Giáo viên - lớp) --------
class TeachingAssignment(Base):
    __tablename__ = "teaching_assignments"

    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"), primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.class_id"), primary_key=True)
    assigned_date = Column(Date, server_default=func.current_date())

    teacher = relationship("Teacher", back_populates="assignments")
    class_ = relationship("Class", back_populates="teaching_assignments")

# -------- GRADE (Điểm học sinh) --------
class Grade(Base):
    __tablename__ = "grades"

    grade_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.class_id"), nullable=False)
    subject = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="grades")
    class_ = relationship("Class", back_populates="grades")
