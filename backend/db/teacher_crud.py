from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from fastapi import HTTPException

from . import models, schemas, teacher_schemas
from datetime import datetime

def get_teacher_classes(db: Session, teacher_id: int) -> List[models.Class]:
    """Lấy danh sách các lớp học mà giáo viên phụ trách"""
    return (db.query(models.Class)
            .join(models.TeachingAssignment)
            .filter(models.TeachingAssignment.teacher_id == teacher_id)
            .all())

def create_class(
    db: Session, 
    teacher_id: int,
    class_data: teacher_schemas.TeacherClassCreate
) -> models.Class:
    """Tạo lớp học mới và gán cho giáo viên"""
    # Tạo lớp học
    db_class = models.Class(
        class_name=class_data.class_name,
        year=class_data.year,
        semester=class_data.semester
    )
    db.add(db_class)
    db.flush()  # Để lấy class_id

    # Tạo assignment cho giáo viên
    db_assignment = models.TeachingAssignment(
        teacher_id=teacher_id,
        class_id=db_class.class_id
    )
    db.add(db_assignment)
    
    db.commit()
    db.refresh(db_class)
    return db_class

def get_class_details(
    db: Session, 
    class_id: int, 
    teacher_id: int
) -> Optional[teacher_schemas.ClassDetails]:
    """Lấy chi tiết lớp học bao gồm danh sách sinh viên và điểm"""
    # Kiểm tra quyền truy cập
    assignment = (db.query(models.TeachingAssignment)
                 .filter(models.TeachingAssignment.class_id == class_id,
                        models.TeachingAssignment.teacher_id == teacher_id)
                 .first())
    if not assignment:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập lớp học này")

    # Lấy thông tin lớp
    db_class = db.query(models.Class).get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")

    # Lấy sinh viên và điểm
    students_with_grades = (
        db.query(models.Student, models.Grade)
        .join(models.Enrollment)
        .outerjoin(models.Grade)
        .filter(models.Enrollment.class_id == class_id)
        .all()
    )

    # Đếm số sinh viên hiện tại
    current_students = (db.query(func.count(models.Enrollment.student_id))
                       .filter(models.Enrollment.class_id == class_id)
                       .scalar())

    # Chuyển đổi sang ClassDetails
    result = teacher_schemas.ClassDetails(
        **db_class.__dict__,
        current_students=current_students,
        max_students=0,  # Cần thêm trường này vào models.Class
        students=[]
    )

    # Thêm thông tin sinh viên và điểm
    for student, grade in students_with_grades:
        result.students.append(
            teacher_schemas.StudentGrade(
                student=student,
                grades=grade if grade else None
            )
        )

    return result

def update_class(
    db: Session,
    class_id: int,
    teacher_id: int,
    update_data: teacher_schemas.TeacherClassUpdate
) -> models.Class:
    """Cập nhật thông tin lớp học"""
    # Kiểm tra quyền
    assignment = (db.query(models.TeachingAssignment)
                 .filter(models.TeachingAssignment.class_id == class_id,
                        models.TeachingAssignment.teacher_id == teacher_id)
                 .first())
    if not assignment:
        raise HTTPException(status_code=403, detail="Không có quyền sửa lớp học này")

    # Cập nhật
    db_class = db.query(models.Class).get(class_id)
    if not db_class:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(db_class, key, value)

    db.commit()
    db.refresh(db_class)
    return db_class

def delete_class(db: Session, class_id: int, teacher_id: int) -> None:
    """Xóa lớp học (chỉ khi chưa có sinh viên đăng ký)"""
    # Kiểm tra quyền
    assignment = (db.query(models.TeachingAssignment)
                 .filter(models.TeachingAssignment.class_id == class_id,
                        models.TeachingAssignment.teacher_id == teacher_id)
                 .first())
    if not assignment:
        raise HTTPException(status_code=403, detail="Không có quyền xóa lớp học này")

    # Kiểm tra có sinh viên không
    has_students = db.query(models.Enrollment).filter_by(class_id=class_id).first()
    if has_students:
        raise HTTPException(status_code=400, detail="Không thể xóa lớp đã có sinh viên")

    # Xóa assignment trước
    db.delete(assignment)
    
    # Xóa lớp
    db_class = db.query(models.Class).get(class_id)
    if db_class:
        db.delete(db_class)
        db.commit()

def add_student_to_class(
    db: Session,
    class_id: int,
    teacher_id: int,
    student_data: teacher_schemas.StudentEnrollment
) -> models.Student:
    """Thêm sinh viên vào lớp"""
    # Kiểm tra quyền
    assignment = (db.query(models.TeachingAssignment)
                 .filter(models.TeachingAssignment.class_id == class_id,
                        models.TeachingAssignment.teacher_id == teacher_id)
                 .first())
    if not assignment:
        raise HTTPException(status_code=403, detail="Không có quyền thêm sinh viên vào lớp này")

    # Tìm sinh viên theo mã
    student = (db.query(models.Student)
              .join(models.User)
              .filter(models.Student.student_code == student_data.student_code)
              .first())

    if not student:
        # Tạo user mới
        new_user = models.User(
            username=student_data.student_code,  # Dùng mã SV làm username
            password="password123",  # Cần hash và tạo mật khẩu ngẫu nhiên
            full_name=student_data.full_name,
            role=models.UserRole.student
        )
        db.add(new_user)
        db.flush()

        # Tạo student profile
        student = models.Student(
            student_id=new_user.user_id,
            student_code=student_data.student_code
        )
        db.add(student)
        db.flush()

    # Kiểm tra đã đăng ký chưa
    existing = (db.query(models.Enrollment)
               .filter_by(student_id=student.student_id, class_id=class_id)
               .first())
    if existing:
        raise HTTPException(status_code=400, detail="Sinh viên đã đăng ký lớp này")

    # Thêm vào lớp
    enrollment = models.Enrollment(
        student_id=student.student_id,
        class_id=class_id
    )
    db.add(enrollment)
    db.commit()

    return student

def remove_student_from_class(
    db: Session,
    class_id: int,
    teacher_id: int,
    student_id: int
) -> None:
    """Xóa sinh viên khỏi lớp"""
    # Kiểm tra quyền
    assignment = (db.query(models.TeachingAssignment)
                 .filter(models.TeachingAssignment.class_id == class_id,
                        models.TeachingAssignment.teacher_id == teacher_id)
                 .first())
    if not assignment:
        raise HTTPException(status_code=403, detail="Không có quyền xóa sinh viên khỏi lớp này")

    # Xóa enrollment
    enrollment = (db.query(models.Enrollment)
                 .filter_by(student_id=student_id, class_id=class_id)
                 .first())
    if enrollment:
        # Xóa điểm nếu có
        db.query(models.Grade).filter_by(
            student_id=student_id,
            class_id=class_id
        ).delete()
        
        db.delete(enrollment)
        db.commit()

def update_student_grades(
    db: Session,
    class_id: int,
    teacher_id: int,
    student_id: int,
    grades: teacher_schemas.GradeUpdate
) -> models.Grade:
    """Cập nhật điểm cho sinh viên"""
    # Kiểm tra quyền
    assignment = (db.query(models.TeachingAssignment)
                 .filter(models.TeachingAssignment.class_id == class_id,
                        models.TeachingAssignment.teacher_id == teacher_id)
                 .first())
    if not assignment:
        raise HTTPException(status_code=403, detail="Không có quyền cập nhật điểm")

    # Kiểm tra sinh viên có trong lớp không
    enrollment = (db.query(models.Enrollment)
                 .filter_by(student_id=student_id, class_id=class_id)
                 .first())
    if not enrollment:
        raise HTTPException(status_code=404, detail="Sinh viên không có trong lớp này")

    # Lấy hoặc tạo bản ghi điểm
    grade = (db.query(models.Grade)
            .filter_by(student_id=student_id, class_id=class_id)
            .first())
            
    if not grade:
        grade = models.Grade(
            student_id=student_id,
            class_id=class_id
        )
        db.add(grade)

    # Cập nhật điểm
    grade_data = grades.dict(exclude_unset=True)
    for field, value in grade_data.items():
        setattr(grade, field, value)

    db.commit()
    db.refresh(grade)
    return grade
