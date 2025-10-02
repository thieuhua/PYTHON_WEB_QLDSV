from pydantic import BaseModel
from typing import List, Optional
from datetime import date



# ví dụ
class ItemBase(BaseModel):
    name: str
    description: str | None = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int

    class Config:
        orm_mode = True

# non_password
class UserBase(BaseModel):
    username: str
    role: str
    name: str

## hassed pass
class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str]
    password: Optional[str]
    role: Optional[str]
    name: Optional[str]

class UserOut(UserBase):
    id: int

    class Config:
        orm_mode = True


# =======================
# Course
# =======================
class CourseBase(BaseModel):
    teacherId: int
    courseName: str

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    teacherId: Optional[int]
    courseName: Optional[str]

class CourseOut(CourseBase):
    courseId: int
    teacher: Optional[UserOut] = None

    class Config:
        orm_mode = True


# =======================
# Student
# =======================
class StudentBase(BaseModel):
    studentId: int
    courseId: int

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    studentId: Optional[int]
    courseId: Optional[int]

class StudentOut(StudentBase):
    id: int
    student_user: Optional[UserOut] = None
    course: Optional[CourseOut] = None

    class Config:
        orm_mode = True


# =======================
# Baithi
# =======================
class BaithiBase(BaseModel):
    tenBaiThi: str
    courseId: int

class BaithiCreate(BaithiBase):
    pass

class BaithiUpdate(BaseModel):
    tenBaiThi: Optional[str]
    courseId: Optional[int]

class BaithiOut(BaithiBase):
    idBaithi: int
    course: Optional[CourseOut] = None

    class Config:
        orm_mode = True


# =======================
# DiemThi
# =======================
class DiemThiBase(BaseModel):
    idBaithi: int
    studentId: int
    date: Optional[date]
    grade: int

class DiemThiCreate(DiemThiBase):
    pass

class DiemThiUpdate(BaseModel):
    idBaithi: Optional[int]
    studentId: Optional[int]
    date: Optional[date]
    grade: Optional[int]

class DiemThiOut(DiemThiBase):
    id: int
    baithi: Optional[BaithiOut] = None
    student: Optional[StudentOut] = None

    class Config:
        orm_mode = True