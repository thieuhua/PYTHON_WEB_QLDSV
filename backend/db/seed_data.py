"""
Script để tạo dữ liệu mẫu cho sinh viên
Chạy: python -m backend.seed_student_data
"""
from . import database, models
from ..routers import jwt_auth
from sqlalchemy.orm import Session
from datetime import date

def clear_data(db: Session):
    """Xóa dữ liệu cũ"""
    print("🗑️  Đang xóa dữ liệu cũ...")
    db.query(models.Grade).delete()
    db.query(models.Enrollment).delete()
    db.query(models.TeachingAssignment).delete()
    db.query(models.Class).delete()
    db.query(models.Student).delete()
    db.query(models.Teacher).delete()
    db.query(models.User).delete()
    db.commit()
    print("✅ Đã xóa dữ liệu cũ")

def seed_users(db: Session):
    """Tạo users mẫu"""
    print("👥 Đang tạo users...")
    
    users = [
        # Admin
        {
            "username": "admin",
            "password": jwt_auth.hash_password("admin123"),
            "full_name": "Quản trị viên",
            "email": "admin@school.edu.vn",
            "role": models.UserRole.admin
        },
        # Teachers
        {
            "username": "teacher1",
            "password": jwt_auth.hash_password("teacher123"),
            "full_name": "Nguyễn Văn Giáo",
            "email": "teacher1@school.edu.vn",
            "role": models.UserRole.teacher
        },
        {
            "username": "teacher2",
            "password": jwt_auth.hash_password("teacher123"),
            "full_name": "Trần Thị Sư",
            "email": "teacher2@school.edu.vn",
            "role": models.UserRole.teacher
        },
        # Students
        {
            "username": "student1",
            "password": jwt_auth.hash_password("student123"),
            "full_name": "Nguyễn Văn An",
            "email": "student1@student.edu.vn",
            "role": models.UserRole.student
        },
        {
            "username": "student2",
            "password": jwt_auth.hash_password("student123"),
            "full_name": "Trần Thị Bình",
            "email": "student2@student.edu.vn",
            "role": models.UserRole.student
        },
        {
            "username": "student3",
            "password": jwt_auth.hash_password("student123"),
            "full_name": "Lê Văn Cường",
            "email": "student3@student.edu.vn",
            "role": models.UserRole.student
        }
    ]
    
    created_users = []
    for user_data in users:
        user = models.User(**user_data)
        db.add(user)
        db.flush()
        created_users.append(user)
    
    db.commit()
    print(f"✅ Đã tạo {len(created_users)} users")
    return created_users

def seed_teachers(db: Session, users):
    """Tạo teacher profiles"""
    print("👨‍🏫 Đang tạo teacher profiles...")
    
    teachers = []
    teacher_users = [u for u in users if u.role == models.UserRole.teacher]
    
    teacher_data = [
        {"department": "Khoa Công nghệ thông tin", "title": "Giảng viên"},
        {"department": "Khoa Toán - Tin", "title": "Phó Giáo sư"}
    ]
    
    for i, user in enumerate(teacher_users):
        teacher = models.Teacher(
            teacher_id=user.user_id,
            **teacher_data[i]
        )
        db.add(teacher)
        teachers.append(teacher)
    
    db.commit()
    print(f"✅ Đã tạo {len(teachers)} teacher profiles")
    return teachers

def seed_students(db: Session, users):
    """Tạo student profiles"""
    print("👨‍🎓 Đang tạo student profiles...")
    
    students = []
    student_users = [u for u in users if u.role == models.UserRole.student]
    
    student_codes = ["SV001234", "SV001235", "SV001236"]
    birthdates = [
        date(2002, 3, 15),
        date(2002, 7, 20),
        date(2002, 11, 5)
    ]
    
    for i, user in enumerate(student_users):
        student = models.Student(
            student_id=user.user_id,
            student_code=student_codes[i],
            birthdate=birthdates[i]
        )
        db.add(student)
        students.append(student)
    
    db.commit()
    print(f"✅ Đã tạo {len(students)} student profiles")
    return students

def seed_classes(db: Session, teachers):
    """Tạo classes và assign teachers"""
    print("📚 Đang tạo classes...")
    
    class_data = [
        {"class_name": "Lập trình Web", "year": 2025, "semester": 1},
        {"class_name": "Cơ sở dữ liệu", "year": 2025, "semester": 1},
        {"class_name": "Cấu trúc dữ liệu và giải thuật", "year": 2025, "semester": 1},
        {"class_name": "Lập trình hướng đối tượng", "year": 2025, "semester": 2},
        {"class_name": "Mạng máy tính", "year": 2025, "semester": 2}
    ]
    
    classes = []
    for data in class_data:
        cls = models.Class(**data)
        db.add(cls)
        db.flush()
        classes.append(cls)
        
        # Assign teacher to class
        teacher = teachers[len(classes) % len(teachers)]
        assignment = models.TeachingAssignment(
            teacher_id=teacher.teacher_id,
            class_id=cls.class_id
        )
        db.add(assignment)
    
    db.commit()
    print(f"✅ Đã tạo {len(classes)} classes")
    return classes

def seed_enrollments(db: Session, students, classes):
    """Đăng ký sinh viên vào lớp"""
    print("📝 Đang đăng ký sinh viên vào lớp...")
    
    enrollments = []
    
    # Student 1: đăng ký 4 lớp (semester 1 và 2)
    for i in [0, 1, 2, 3]:
        enrollment = models.Enrollment(
            student_id=students[0].student_id,
            class_id=classes[i].class_id,
            enroll_date=date(2025, 1, 10)
        )
        db.add(enrollment)
        enrollments.append(enrollment)
    
    # Student 2: đăng ký 3 lớp (chỉ semester 1)
    for i in [0, 1, 2]:
        enrollment = models.Enrollment(
            student_id=students[1].student_id,
            class_id=classes[i].class_id,
            enroll_date=date(2025, 1, 10)
        )
        db.add(enrollment)
        enrollments.append(enrollment)
    
    # Student 3: đăng ký 2 lớp
    for i in [1, 4]:
        enrollment = models.Enrollment(
            student_id=students[2].student_id,
            class_id=classes[i].class_id,
            enroll_date=date(2025, 1, 10)
        )
        db.add(enrollment)
        enrollments.append(enrollment)
    
    db.commit()
    print(f"✅ Đã tạo {len(enrollments)} enrollments")
    return enrollments

def seed_grades(db: Session, students, classes):
    """Tạo điểm cho sinh viên"""
    print("📊 Đang tạo điểm...")
    
    grades = []
    
    # Điểm cho student 1
    grade_data_s1 = [
        {"class_idx": 0, "subject": "Lập trình Web", "score": 8.5},
        {"class_idx": 1, "subject": "Cơ sở dữ liệu", "score": 9.0},
        {"class_idx": 2, "subject": "Cấu trúc dữ liệu", "score": 7.5},
        {"class_idx": 3, "subject": "Lập trình OOP", "score": 8.0}
    ]
    
    for data in grade_data_s1:
        grade = models.Grade(
            student_id=students[0].student_id,
            class_id=classes[data["class_idx"]].class_id,
            subject=data["subject"],
            score=data["score"]
        )
        db.add(grade)
        grades.append(grade)
    
    # Điểm cho student 2
    grade_data_s2 = [
        {"class_idx": 0, "subject": "Lập trình Web", "score": 9.5},
        {"class_idx": 1, "subject": "Cơ sở dữ liệu", "score": 8.5},
        {"class_idx": 2, "subject": "Cấu trúc dữ liệu", "score": 9.0}
    ]
    
    for data in grade_data_s2:
        grade = models.Grade(
            student_id=students[1].student_id,
            class_id=classes[data["class_idx"]].class_id,
            subject=data["subject"],
            score=data["score"]
        )
        db.add(grade)
        grades.append(grade)
    
    # Điểm cho student 3
    grade_data_s3 = [
        {"class_idx": 1, "subject": "Cơ sở dữ liệu", "score": 7.0},
        {"class_idx": 4, "subject": "Mạng máy tính", "score": 8.0}
    ]
    
    for data in grade_data_s3:
        grade = models.Grade(
            student_id=students[2].student_id,
            class_id=classes[data["class_idx"]].class_id,
            subject=data["subject"],
            score=data["score"]
        )
        db.add(grade)
        grades.append(grade)
    
    db.commit()
    print(f"✅ Đã tạo {len(grades)} grades")
    return grades

def main():
    print("🚀 Bắt đầu seed dữ liệu...")
    print("=" * 50)
    
    # Tạo database
    models.Base.metadata.create_all(bind=database.engine)
    
    db = database.SessionLocal()
    try:
        # Xóa dữ liệu cũ
        clear_data(db)
        
        # Tạo dữ liệu mới
        users = seed_users(db)
        teachers = seed_teachers(db, users)
        students = seed_students(db, users)
        classes = seed_classes(db, teachers)
        enrollments = seed_enrollments(db, students, classes)
        grades = seed_grades(db, students, classes)
        
        print("=" * 50)
        print("✅ HOÀN THÀNH!")
        print("\n📝 Tài khoản đăng nhập:")
        print("  Admin: admin / admin123")
        print("  Teacher: teacher1 / teacher123")
        print("  Student 1: student1 / student123")
        print("  Student 2: student2 / student123")
        print("  Student 3: student3 / student123")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()