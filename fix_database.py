from backend.db import models, database, crud, schemas
from backend.routers import jwt_auth
from sqlalchemy.exc import IntegrityError

# Tạo bảng nếu chưa có
models.Base.metadata.create_all(bind=database.engine)

# Tạo session
db = database.SessionLocal()

def createUser(username, password, role="student"):
    """Hàm tạo user, bỏ qua nếu username đã tồn tại"""
    hashedpassw = jwt_auth.hash_password(password)
    existing_user = db.query(models.User).filter(models.User.username == username).first()

    if existing_user:
        print(f"⚠️ User '{username}' đã tồn tại, bỏ qua.")
        return

    user_db = schemas.UserCreate(
        username=username,
        password=hashedpassw,
        role=role,
        full_name=username
    )

    try:
        crud.create_user(db, user_db)
        print(f"✅ Tạo user '{username}' ({role}) thành công.")
    except IntegrityError:
        db.rollback()
        print(f"⚠️ User '{username}' đã tồn tại, bỏ qua.")
    except Exception as e:
        db.rollback()
        print("❌ Lỗi khi tạo user:", e)

# Tạo admin
createUser("admin", "123", "admin")

# Danh sách student và teacher
st = [
    ("student01", "student"),
    ("student02", "student"),
    ("student03", "student"),
    ("student04", "student"),
    ("teacher01", "teacher"),
    ("teacher02", "teacher"),
    ("teacher03", "teacher"),
    ("teacher04", "teacher"),
]

# Tạo user hàng loạt
for u, r in st:
    createUser(u, "123", r)

# Đóng session
db.close()
