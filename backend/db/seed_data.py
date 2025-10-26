from backend.db import database, models
from sqlalchemy.orm import Session
from datetime import date

def seed_data():
    db: Session = database.SessionLocal()

    # --- Tạo User ---
    user = models.User(
        username="nghia123",
        password="123456",  # sau này sẽ hash
        full_name="Nguyễn Văn Nghĩa",
        email="nghia@example.com",
        role=models.UserRole.student
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # --- Tạo Student liên kết với User ---
    student = models.Student(
        student_id=user.user_id,
        student_code="SV001234",
        birthdate=date(2002, 12, 12)
    )
    db.add(student)

    # --- Tạo Class ---
    class1 = models.Class(class_name="Lập trình Web", year=2025, semester=1)
    class2 = models.Class(class_name="Cơ sở dữ liệu", year=2025, semester=1)
    db.add_all([class1, class2])
    db.commit()

    # --- Ghi danh ---
    enrollment = models.Enrollment(student_id=student.student_id, class_id=class1.class_id)
    db.add(enrollment)
    db.commit()

    # --- Thêm điểm ---
    grade1 = models.Grade(
        student_id=student.student_id,
        class_id=class1.class_id,
        subject="Lập trình Web",
        score=8.5
    )
    grade2 = models.Grade(
        student_id=student.student_id,
        class_id=class2.class_id,
        subject="Cơ sở dữ liệu",
        score=8.0
    )
    db.add_all([grade1, grade2])
    db.commit()

    db.close()
    print("✅ Dữ liệu mẫu đã được thêm thành công!")

if __name__ == "__main__":
    models.Base.metadata.create_all(bind=database.engine)
    seed_data()
