# backend/routers/teacher.py - FIXED VERSION
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import io

from ..db import teacher_crud, crud, database, schemas, models
from ..db.database import get_db
from ..routers import jwt_auth

router = APIRouter(
    prefix="/teacher",
    tags=["Teacher"]
)


# ✅ THÊM SCHEMA MỚI CHO GRADE UPDATE
class GradeUpdateRequest(BaseModel):
    student_id: int
    class_id: int
    subject: str
    score: float = Field(ge=0, le=10, description="Điểm từ 0-10")

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": 1,
                "class_id": 4,
                "subject": "attendance",
                "score": 8.5
            }
        }


# --- Dependency: get current teacher user from Authorization header (Bearer <token>) ---
def get_current_teacher(request: Request, db: Session = Depends(get_db)):
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
    return [
        {
            "class_id": c.class_id,
            "class_name": c.class_name,
            "year": c.year,
            "semester": c.semester,
        } for c in cls
    ]


@router.post("/classes", summary="Create class and assign to current teacher")
def create_class(class_in: schemas.ClassCreate, current_user: models.User = Depends(get_current_teacher),
                 db: Session = Depends(get_db)):
    teacher_id = current_user.user_id
    newc = teacher_crud.create_class_for_teacher(db, teacher_id, class_in)
    return {"class_id": newc.class_id}


@router.get("/classes/{class_id}", summary="Get class detail (students + grades)")
def get_class(class_id: int, current_user: models.User = Depends(get_current_teacher), db: Session = Depends(get_db)):
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
def add_student(class_id: int, payload: dict, current_user: models.User = Depends(get_current_teacher),
                db: Session = Depends(get_db)):
    full_name = payload.get("full_name")
    student_code = payload.get("student_code")
    if not student_code or not full_name:
        raise HTTPException(status_code=400, detail="full_name and student_code required")

    ta = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_id == class_id,
        models.TeachingAssignment.teacher_id == current_user.user_id
    ).first()
    if not ta:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")

    info = teacher_crud.add_student_to_class(db, class_id, full_name, student_code)
    return info


@router.delete("/classes/{class_id}/students/{student_id}", summary="Unenroll student from a class")
def delete_student(class_id: int, student_id: int, current_user: models.User = Depends(get_current_teacher),
                   db: Session = Depends(get_db)):
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


# ✅ SỬA ENDPOINT NÀY - Dùng schema mới và xử lý đúng
@router.post("/classes/{class_id}/grades", summary="Save/update grades (bulk)")
def save_grades(
        class_id: int,
        grades: List[GradeUpdateRequest],  # ✅ Dùng schema mới
        current_user: models.User = Depends(get_current_teacher),
        db: Session = Depends(get_db)
):
    """
    Update điểm cho sinh viên trong lớp
    Body: List of {student_id, class_id, subject, score}
    """
    # Verify teacher assigned to class
    ta = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_id == class_id,
        models.TeachingAssignment.teacher_id == current_user.user_id
    ).first()
    if not ta:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")

    # ✅ Validate class_id khớp với URL
    for grade_data in grades:
        if grade_data.class_id != class_id:
            raise HTTPException(
                status_code=400,
                detail=f"class_id in body ({grade_data.class_id}) must match URL parameter ({class_id})"
            )

    # ✅ Convert sang dict để gọi teacher_crud
    payload = [g.model_dump() for g in grades]

    try:
        teacher_crud.save_grades(db, class_id, payload)
        return {
            "ok": True,
            "message": f"Updated {len(grades)} grade(s) successfully",
            "updated_count": len(grades)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save grades: {str(e)}")


@router.delete("/classes/{class_id}", summary="Delete a class")
def delete_class(
        class_id: int,
        current_user: models.User = Depends(get_current_teacher),
        db: Session = Depends(get_db)
):
    """
    Xóa lớp học và tất cả dữ liệu liên quan (sinh viên, điểm, join codes).
    Chỉ giáo viên được gán mới có thể xóa lớp.
    """
    success = teacher_crud.delete_class(db, class_id, current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Class not found or you don't have permission to delete it"
        )
    return {"ok": True, "message": "Class deleted successfully"}


@router.get("/classes/{class_id}/export", summary="Export students to CSV")
def export_students(
        class_id: int,
        current_user: models.User = Depends(get_current_teacher),
        db: Session = Depends(get_db)
):
    """
    Export danh sách sinh viên và điểm số ra file CSV.
    """
    try:
        # ✅ csv_bytes is already UTF-8 encoded bytes with BOM
        csv_bytes = teacher_crud.export_students_csv(db, class_id, current_user.user_id)

        # Get class name for filename
        cls = db.query(models.Class).filter(models.Class.class_id == class_id).first()
        class_name = cls.class_name if cls else f"class_{class_id}"
        # Clean filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in class_name)
        filename = f"{safe_name}_students.csv"


        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except ValueError as e:
        # Class not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/classes/{class_id}/import", summary="Import students from CSV")
async def import_students(
        class_id: int,
        file: UploadFile = File(...),
        current_user: models.User = Depends(get_current_teacher),
        db: Session = Depends(get_db)
):
    """
    Import danh sách sinh viên và điểm số từ file CSV.
    Format: Họ tên, Mã SV, Chuyên cần, Giữa kỳ, Cuối kỳ
    hoặc: STT, Họ tên, Mã SV, Chuyên cần, Giữa kỳ, Cuối kỳ, Trung bình
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")

    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8-sig')  # utf-8-sig to handle BOM

        # Import
        result = teacher_crud.import_students_csv(db, class_id, current_user.user_id, csv_content)

        return {
            "ok": True,
            "message": f"Import completed: {result['success_count']} thành công, {result['error_count']} lỗi",
            "success_count": result['success_count'],
            "error_count": result['error_count'],
            "errors": result['errors']
        }
    except ValueError as e:
        # Class not found
        raise HTTPException(status_code=404, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please use UTF-8 encoding")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


