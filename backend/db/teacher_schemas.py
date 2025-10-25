from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from .schemas import StudentRead, ClassRead, GradeRead

class TeacherClassCreate(BaseModel):
    class_name: str = Field(..., min_length=1)
    max_students: int = Field(..., gt=0, le=200)
    year: int = Field(..., gt=2000)
    semester: int = Field(..., ge=1, le=2)

class TeacherClassUpdate(BaseModel):
    class_name: Optional[str] = None
    max_students: Optional[int] = None

class TeacherClassWithStats(ClassRead):
    current_students: int
    max_students: int
    
    class Config:
        orm_mode = True

class StudentEnrollment(BaseModel):
    student_code: str
    full_name: str

class GradeUpdate(BaseModel):
    attendance: Optional[float] = Field(None, ge=0, le=10)  # Điểm chuyên cần
    midterm: Optional[float] = Field(None, ge=0, le=10)     # Điểm giữa kỳ
    final: Optional[float] = Field(None, ge=0, le=10)       # Điểm cuối kỳ

class StudentGrade(BaseModel):
    student: StudentRead
    grades: GradeRead

class ClassDetails(TeacherClassWithStats):
    students: List[StudentGrade] = []

    class Config:
        orm_mode = True

# For CSV import/export
class StudentGradeImport(BaseModel):
    student_code: str
    full_name: str
    attendance: Optional[float] = None
    midterm: Optional[float] = None
    final: Optional[float] = None
