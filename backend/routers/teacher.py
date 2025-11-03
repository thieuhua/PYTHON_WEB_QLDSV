# backend/routers/teacher.py - FIXED FULL VERSION
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from typing import List
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import csv
import io
import re
from urllib.parse import quote

from ..db import teacher_crud, crud, database, schemas, models
from ..db.database import get_db
from ..routers import jwt_auth

router = APIRouter(
    prefix="/teacher",
    tags=["Teacher"]
)


# ✅ SCHEMA CHO CẬP NHẬT ĐIỂM
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


# ✅ DEPENDENCY - LẤY GIẢNG VIÊN TỪ TOKEN
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
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    db_user = crud.get_user_by_username(db, username)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if db_user.role != schemas.UserRole.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requires teacher role")
    return db_user


# ================== ROUTES ==================

@router.get("/classes", summary="Get classes for current teacher")
def list_classes(current_user: models.User = Depends(get_current_teacher), db: Session = Depends(get_db)):
    teacher_id = current_user.user_id
    cls = teacher_crud.get_teacher_classes(db, teacher_id)

    result = []
    for c in cls:
        # ✅ Đếm số sinh viên trong lớp
        student_count = db.query(models.Enrollment).filter(models.Enrollment.class_id == c.class_id).count()

        result.append({
            "class_id": c.class_id,
            "class_name": c.class_name,
            "year": c.year,
            "semester": c.semester,
            "current_students": student_count
        })
    return result


@router.post("/classes", summary="Create class and assign to current teacher")
def create_class(class_in: schemas.ClassCreate,
                 current_user: models.User = Depends(get_current_teacher),
                 db: Session = Depends(get_db)):
    teacher_id = current_user.user_id
    newc = teacher_crud.create_class_for_teacher(db, teacher_id, class_in)
    return {"class_id": newc.class_id}


@router.get("/classes/{class_id}", summary="Get class detail (students + grades)")
def get_class(class_id: int,
              current_user: models.User = Depends(get_current_teacher),
              db: Session = Depends(get_db)):
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
def add_student(class_id: int,
                payload: dict,
                current_user: models.User = Depends(get_current_teacher),
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
def delete_student(class_id: int,
                   student_id: int,
                   current_user: models.User = Depends(get_current_teacher),
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


@router.post("/classes/{class_id}/grades", summary="Save/update grades (bulk)")
def save_grades(class_id: int,
                grades: List[GradeUpdateRequest],
                current_user: models.User = Depends(get_current_teacher),
                db: Session = Depends(get_db)):
    """
    Update điểm cho sinh viên trong lớp
    Body: List of {student_id, class_id, subject, score}
    """
    ta = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_id == class_id,
        models.TeachingAssignment.teacher_id == current_user.user_id
    ).first()
    if not ta:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")

    for grade_data in grades:
        if grade_data.class_id != class_id:
            raise HTTPException(
                status_code=400,
                detail=f"class_id in body ({grade_data.class_id}) must match URL parameter ({class_id})"
            )

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


@router.delete("/classes/{class_id}", summary="Delete a class and its enrollments")
def delete_class(class_id: int,
                 current_user: models.User = Depends(get_current_teacher),
                 db: Session = Depends(get_db)):
    """
    Xóa lớp học do giáo viên sở hữu, bao gồm enrollment, assignment, join code, và điểm.
    """
    # Kiểm tra quyền sở hữu
    ta = (
        db.query(models.TeachingAssignment)
        .filter(
            models.TeachingAssignment.class_id == class_id,
            models.TeachingAssignment.teacher_id == current_user.user_id
        )
        .first()
    )
    if not ta:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this class or lack permission"
        )

    cls = db.query(models.Class).filter(models.Class.class_id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    try:
        # Xóa Enrollment
        db.query(models.Enrollment).filter(models.Enrollment.class_id == class_id).delete(synchronize_session=False)

        # Xóa TeachingAssignment
        db.query(models.TeachingAssignment).filter(models.TeachingAssignment.class_id == class_id).delete(synchronize_session=False)

        # Xóa JoinCode (mã tham gia lớp)
        if hasattr(models, "JoinCode"):
            db.query(models.JoinCode).filter(models.JoinCode.class_id == class_id).delete(synchronize_session=False)
        elif hasattr(models, "Join_Code"):
            db.query(models.Join_Code).filter(models.Join_Code.class_id == class_id).delete(synchronize_session=False)

        # Xóa bảng điểm (nếu có)
        if hasattr(models, "Grade"):
            db.query(models.Grade).filter(models.Grade.class_id == class_id).delete(synchronize_session=False)
        elif hasattr(models, "Score"):
            db.query(models.Score).filter(models.Score.class_id == class_id).delete(synchronize_session=False)

        # Xóa lớp
        db.delete(cls)
        db.commit()
        return {"ok": True, "message": f"Class {class_id} deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete class: {str(e)}")


@router.get("/classes/{class_id}/export", summary="Export student list to CSV")
def export_class_students(
    class_id: int,
    current_user: models.User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Export danh sách sinh viên của lớp ra file CSV với encoding UTF-8 BOM để hỗ trợ tiếng Việt
    """
    try:
        # Kiểm tra quyền truy cập
        ta = db.query(models.TeachingAssignment).filter(
            models.TeachingAssignment.class_id == class_id,
            models.TeachingAssignment.teacher_id == current_user.user_id
        ).first()
        if not ta:
            raise HTTPException(status_code=403, detail="You are not assigned to this class")

        # Lấy thông tin lớp và sinh viên
        class_detail = teacher_crud.get_class_detail(db, class_id)
        if not class_detail:
            raise HTTPException(status_code=404, detail="Class not found")

        # Tạo CSV với UTF-8 BOM
        output = io.StringIO()
        # Thêm BOM để Excel nhận diện UTF-8
        output.write('\ufeff')

        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        # Header
        writer.writerow(['STT', 'Họ và tên', 'Mã sinh viên', 'Chuyên cần', 'Giữa kỳ', 'Cuối kỳ', 'Trung bình'])

        # Data
        for idx, student in enumerate(class_detail.get('students', []), start=1):
            grades = student.get('grades', {})
            att = grades.get('attendance', '')
            mid = grades.get('mid', '')
            fin = grades.get('final', '')

            # Tính điểm trung bình
            avg = ''
            if att != '' and mid != '' and fin != '':
                try:
                    avg = round(float(att) * 0.2 + float(mid) * 0.3 + float(fin) * 0.5, 1)
                except:
                    avg = ''

            writer.writerow([
                idx,
                student.get('full_name', ''),
                student.get('student_code', ''),
                att,
                mid,
                fin,
                avg
            ])

        # Lấy nội dung CSV
        csv_content = output.getvalue()

        # Sanitize filename - loại bỏ ký tự đặc biệt
        class_name = class_detail.get("class_name", "class")
        # Loại bỏ ký tự không hợp lệ trong tên file
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', class_name)
        filename = f"{safe_filename}_students.csv"

        # Encode filename cho Content-Disposition (RFC 5987)
        filename_encoded = quote(filename)

        # Encode content sang bytes với UTF-8 BOM
        csv_bytes = csv_content.encode('utf-8-sig')

        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename_encoded}',
            'Content-Type': 'text/csv; charset=utf-8',
            'Cache-Control': 'no-cache'
        }

        # Dùng Response thay vì StreamingResponse để tránh lỗi encoding
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers=headers
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Export failed: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ Export error: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/classes/{class_id}/import", summary="Import students from CSV")
async def import_class_students(
    class_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Import danh sách sinh viên từ file CSV
    Format: STT,Họ và tên,Mã sinh viên
    hoặc: Họ và tên,Mã sinh viên
    """
    # Kiểm tra quyền truy cập
    ta = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_id == class_id,
        models.TeachingAssignment.teacher_id == current_user.user_id
    ).first()
    if not ta:
        raise HTTPException(status_code=403, detail="You are not assigned to this class")

    # Kiểm tra file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        # Đọc file với nhiều encoding khác nhau
        content = await file.read()

        # Thử decode với các encoding khác nhau
        text_content = None
        for encoding in ['utf-8-sig', 'utf-8', 'cp1252', 'latin1']:
            try:
                text_content = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text_content is None:
            raise HTTPException(status_code=400, detail="Cannot decode file. Please use UTF-8 encoding")

        # Parse CSV
        csv_reader = csv.reader(io.StringIO(text_content))
        rows = list(csv_reader)

        if len(rows) < 2:
            raise HTTPException(status_code=400, detail="CSV file is empty or missing header")

        # Bỏ qua header
        data_rows = rows[1:]

        added_count = 0
        errors = []

        for idx, row in enumerate(data_rows, start=2):
            if not row or len(row) < 2:
                continue

            # Xác định vị trí của tên và mã SV
            # Nếu có STT ở cột đầu thì tên ở cột 1, mã ở cột 2
            # Ngược lại tên ở cột 0, mã ở cột 1
            if len(row) >= 3 and row[0].strip().isdigit():
                full_name = row[1].strip()
                student_code = row[2].strip()
            else:
                full_name = row[0].strip()
                student_code = row[1].strip()

            if not full_name or not student_code:
                errors.append(f"Row {idx}: Missing name or student code")
                continue

            try:
                teacher_crud.add_student_to_class(db, class_id, full_name, student_code)
                added_count += 1
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        return {
            "ok": True,
            "message": f"Successfully imported {added_count} students",
            "added_count": added_count,
            "total_rows": len(data_rows),
            "errors": errors if errors else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import: {str(e)}")
