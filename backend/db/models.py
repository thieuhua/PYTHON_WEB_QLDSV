from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .database import Base
import enum

class UserRole(str, enum.Enum):  # Vai trò người dùng
    admin = "admin"
    teacher = "teacher"
    student = "student"

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)


# Bảng User
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default= UserRole.student)  # e.g., "teacher" or "student"
    
    # Quan hệ
    courses_taught = relationship("Course", back_populates="teacher")  # giáo viên dạy các khóa
    student_courses = relationship("Student", back_populates="student_user")  # nếu user là student

# Bảng Course
class Course(Base):
    __tablename__ = "courses"
    
    courseId = Column(Integer, primary_key=True)
    teacherId = Column(Integer, ForeignKey("users.id"))  # liên kết giáo viên
    courseName = Column(String, nullable=False)
    
    teacher = relationship("User", back_populates="courses_taught")
    students = relationship("Student", back_populates="course")
    baithis = relationship("Baithi", back_populates="course")

# Bảng Student (liên kết User với Course)
class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True)
    studentId = Column(Integer, ForeignKey("users.id"))  # liên kết User
    courseId = Column(Integer, ForeignKey("courses.courseId"))  # liên kết Course
    
    student_user = relationship("User", back_populates="student_courses")
    course = relationship("Course", back_populates="students")
    diem_this = relationship("DiemThi", back_populates="student")

# Bảng Baithi (đề thi)
class Baithi(Base):
    __tablename__ = "baithis"
    
    idBaithi = Column(Integer, primary_key=True)
    tenBaiThi = Column(String, nullable=False)
    courseId = Column(Integer, ForeignKey("courses.courseId"))  # liên kết khóa học
    
    course = relationship("Course", back_populates="baithis")
    diem_this = relationship("DiemThi", back_populates="baithi")

# Bảng DiemThi
class DiemThi(Base):
    __tablename__ = "diemthis"
    
    id = Column(Integer, primary_key=True)
    idBaithi = Column(Integer, ForeignKey("baithis.idBaithi"))
    studentId = Column(Integer, ForeignKey("students.id"))
    date = Column(Date)
    grade = Column(Integer)
    
    baithi = relationship("Baithi", back_populates="diem_this")
    student = relationship("Student", back_populates="diem_this")

# Tạo bảng
# Base.metadata.create_all(engine)