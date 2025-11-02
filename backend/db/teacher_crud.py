# backend/db/teacher_crud.py
from typing import List, Dict, Optional, Tuple
import secrets
from sqlalchemy.orm import Session
from sqlalchemy import and_
import random
import csv
import io
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
        semester=class_in.semester,
        max_students=getattr(class_in, 'max_students', 50)  # Sử dụng max_students từ input hoặc mặc định 50
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    # Tao code vao lop
    def generate_code():
        characters = "1234567890QWERTYUIOPASDFGHJKLZXCVBNM"
        while True:
            code = ""
            for i in range(6):
                code += random.choice(characters)
            if db.query(models.JoinCode).filter(models.JoinCode.code == code).first() is None:
                return code

    random_code = generate_code()
    db_joincode = models.JoinCode(
        code=random_code,
        class_id=new_class.class_id
    )
    db.add(db_joincode)
    db.commit()
    db.refresh(db_joincode)
    
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
        "join_code":cls.join_codes[0].code if cls.join_codes else None,
        "max_students": cls.max_students if cls.max_students else 50,  # Trả về max_students từ database
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


# --- Delete a class ---
def delete_class(db: Session, class_id: int, teacher_id: int) -> bool:
    """
    Delete a class and all related data (enrollments, grades, join codes, teaching assignments).
    Only the assigned teacher can delete the class.
    """
    # Verify teacher is assigned to this class
    ta = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.class_id == class_id,
        models.TeachingAssignment.teacher_id == teacher_id
    ).first()
    if not ta:
        return False

    # Get the class
    cls = db.query(models.Class).filter(models.Class.class_id == class_id).first()
    if not cls:
        return False

    # Delete all related data in order
    # 1. Delete grades
    db.query(models.Grade).filter(models.Grade.class_id == class_id).delete()

    # 2. Delete enrollments
    db.query(models.Enrollment).filter(models.Enrollment.class_id == class_id).delete()

    # 3. Delete join codes
    db.query(models.JoinCode).filter(models.JoinCode.class_id == class_id).delete()

    # 4. Delete teaching assignments
    db.query(models.TeachingAssignment).filter(models.TeachingAssignment.class_id == class_id).delete()

    # 5. Finally delete the class
    db.delete(cls)
    db.commit()

    return True


# --- Export class students to CSV ---
def export_students_csv(db: Session, class_id: int, teacher_id: int) -> bytes:
    """
    Export students and grades from a class to CSV format.
    Returns CSV content as UTF-8 encoded bytes with BOM.
    """

    # Get class detail with students and grades
    detail = get_class_detail(db, class_id)
    if not detail:
        raise ValueError("Class not found")

    # Create CSV in memory using StringIO first
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['STT', 'Họ tên', 'Mã SV', 'Chuyên cần', 'Giữa kỳ', 'Cuối kỳ', 'Trung bình'])

    # Write student data
    for idx, student in enumerate(detail['students'], 1):
        grades = student.get('grades', {})
        att = grades.get('attendance', '')
        mid = grades.get('mid', '')
        final = grades.get('final', '')

        # Calculate average
        avg = ''
        if att and mid and final:
            try:
                avg = round(float(att) * 0.2 + float(mid) * 0.3 + float(final) * 0.5, 2)
            except (ValueError, TypeError):
                avg = ''

        writer.writerow([
            idx,
            student.get('full_name', ''),
            student.get('student_code', ''),
            att,
            mid,
            final,
            avg
        ])

    csv_string = output.getvalue()
    output.close()

    # ✅ Encode to UTF-8 with BOM for Excel compatibility
    csv_bytes = ('\ufeff' + csv_string).encode('utf-8')

    return csv_bytes


# --- Import students from CSV ---
def import_students_csv(db: Session, class_id: int, teacher_id: int, csv_content: str) -> Dict:
    """
    Import students and grades from CSV content.
    CSV format: Họ tên, Mã SV, Chuyên cần, Giữa kỳ, Cuối kỳ
    Returns dict with success/error counts.
    """
    # Verify class exists
    cls = db.query(models.Class).filter(models.Class.class_id == class_id).first()
    if not cls:
        raise ValueError("Class not found")

    # Parse CSV
    input_stream = io.StringIO(csv_content)
    reader = csv.reader(input_stream)

    # Skip header if exists
    first_row = next(reader, None)
    if first_row and (first_row[0].lower() in ['stt', 'họ tên', 'ho ten', 'full_name']):
        # This is a header row, continue to next
        pass
    else:
        # First row is data, process it
        input_stream.seek(0)
        reader = csv.reader(input_stream)

    success_count = 0
    error_count = 0
    errors = []

    for row_num, row in enumerate(reader, 1):
        try:
            # Skip empty rows
            if not row or all(not cell.strip() for cell in row):
                continue

            # Handle different CSV formats
            if len(row) < 2:
                errors.append(f"Dòng {row_num}: Thiếu thông tin (cần ít nhất Họ tên và Mã SV)")
                error_count += 1
                continue

            # Parse based on number of columns
            if row[0].isdigit():  # First column is STT
                if len(row) < 3:
                    errors.append(f"Dòng {row_num}: Thiếu thông tin")
                    error_count += 1
                    continue
                full_name = row[1].strip()
                student_code = row[2].strip()
                att = row[3].strip() if len(row) > 3 else ''
                mid = row[4].strip() if len(row) > 4 else ''
                final = row[5].strip() if len(row) > 5 else ''
            else:  # No STT column
                full_name = row[0].strip()
                student_code = row[1].strip()
                att = row[2].strip() if len(row) > 2 else ''
                mid = row[3].strip() if len(row) > 3 else ''
                final = row[4].strip() if len(row) > 4 else ''

            if not full_name or not student_code:
                errors.append(f"Dòng {row_num}: Thiếu họ tên hoặc mã SV")
                error_count += 1
                continue

            # Add student to class
            try:
                add_student_to_class(db, class_id, full_name, student_code)
            except Exception as e:
                # Student might already exist, that's ok
                pass

            # Get student ID
            user = crud.get_user_by_username(db, student_code)
            if not user:
                errors.append(f"Dòng {row_num}: Không tìm thấy sinh viên {student_code}")
                error_count += 1
                continue

            # Add grades if provided
            grades_to_save = []

            if att:
                try:
                    att_score = float(att)
                    if 0 <= att_score <= 10:
                        grades_to_save.append({
                            'student_id': user.user_id,
                            'subject': 'attendance',
                            'score': att_score
                        })
                except ValueError:
                    errors.append(f"Dòng {row_num}: Điểm chuyên cần không hợp lệ: {att}")

            if mid:
                try:
                    mid_score = float(mid)
                    if 0 <= mid_score <= 10:
                        grades_to_save.append({
                            'student_id': user.user_id,
                            'subject': 'mid',
                            'score': mid_score
                        })
                except ValueError:
                    errors.append(f"Dòng {row_num}: Điểm giữa kỳ không hợp lệ: {mid}")

            if final:
                try:
                    final_score = float(final)
                    if 0 <= final_score <= 10:
                        grades_to_save.append({
                            'student_id': user.user_id,
                            'subject': 'final',
                            'score': final_score
                        })
                except ValueError:
                    errors.append(f"Dòng {row_num}: Điểm cuối kỳ không hợp lệ: {final}")

            # Save grades
            if grades_to_save:
                save_grades(db, class_id, grades_to_save)

            success_count += 1

        except Exception as e:
            errors.append(f"Dòng {row_num}: Lỗi - {str(e)}")
            error_count += 1

    return {
        'success_count': success_count,
        'error_count': error_count,
        'errors': errors
    }


