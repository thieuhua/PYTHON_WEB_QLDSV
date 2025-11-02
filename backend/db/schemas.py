from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import List, Optional
from enum import Enum


# -------------------------------
# ENUM
# -------------------------------
class UserRole(str, Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"


# -------------------------------
# USER SCHEMAS
# -------------------------------
class UserBase(BaseModel):
    username: str
    full_name: str
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.student


class UserCreate(UserBase):
    password: str
    # Student fields
    student_code: Optional[str] = None
    birthdate: Optional[date] = None
    # Teacher fields
    department: Optional[str] = None
    title: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None
    # [SỬA] Thêm student_code để cho phép update mã sinh viên
    student_code: Optional[str] = None
    # student/teacher profile fields for updating
    birthdate: Optional[date] = None
    department: Optional[str] = None
    title: Optional[str] = None


class UserRead(UserBase):
    user_id: int

    class Config:
        orm_mode = True


# -------------------------------
# TEACHER SCHEMAS
# -------------------------------
class TeacherBase(BaseModel):
    department: Optional[str] = None
    title: Optional[str] = None


class TeacherCreate(TeacherBase):
    user_id: int


class TeacherRead(TeacherBase):
    teacher_id: int
    user: Optional[UserRead]

    class Config:
        orm_mode = True


# -------------------------------
# STUDENT SCHEMAS
# -------------------------------
class StudentBase(BaseModel):
    student_code: Optional[str] = None
    birthdate: Optional[date] = None


class StudentCreate(StudentBase):
    user_id: int


class StudentRead(StudentBase):
    student_id: int
    user: Optional[UserRead]

    class Config:
        orm_mode = True


# -------------------------------
# CLASS SCHEMAS
# -------------------------------
class ClassBase(BaseModel):
    class_name: str
    year: int
    semester: int


class ClassCreate(ClassBase):
    max_students: Optional[int] = 50  # Số lượng sinh viên tối đa, mặc định 50


class ClassRead(ClassBase):
    class_id: int
    max_students: Optional[int] = None

    class Config:
        orm_mode = True


# -------------------------------
# ENROLLMENT SCHEMAS (student-class)
# -------------------------------
class EnrollmentBase(BaseModel):
    student_id: int
    class_id: int


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentRead(EnrollmentBase):
    enroll_date: date

    class Config:
        orm_mode = True


# -------------------------------
# TEACHING ASSIGNMENT SCHEMAS (teacher-class)
# -------------------------------
class TeachingAssignmentBase(BaseModel):
    teacher_id: int
    class_id: int


class TeachingAssignmentCreate(TeachingAssignmentBase):
    pass


class TeachingAssignmentRead(TeachingAssignmentBase):
    assigned_date: date

    class Config:
        orm_mode = True


# -------------------------------
# GRADE SCHEMAS
# -------------------------------
class GradeBase(BaseModel):
    student_id: int
    class_id: int
    subject: str
    score: float = Field(ge=0, le=10, description="Điểm phải trong khoảng 0–10")


class GradeCreate(GradeBase):
    pass


class GradeUpdate(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=10)


class GradeRead(GradeBase):
    grade_id: int
    updated_at: datetime

    class Config:
        orm_mode = True


# Composite view for /me
class MeRead(UserRead):
    student_profile: Optional[StudentRead] = None
    teacher_profile: Optional[TeacherRead] = None

    class Config:
        orm_mode = True

#Join code schema
class JoinCode(BaseModel):
    code: str

    class Config:
        orm_mode=True