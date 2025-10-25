from backend.db import models, database, crud, schemas
from backend.routers import jwt_auth
models.Base.metadata.create_all(bind=database.engine)

# db = database.SessionLocal()
db = database.SessionLocal()
def createUser(username, password, role = "student"):
    hashedpassw: str = jwt_auth.hash_password(password)
    user_db = schemas.UserCreate(username=username, password=hashedpassw, role=role, full_name=username)
    try:
        crud.create_user(db, user_db)
    except Exception as e:
        print("Lỗi khi tạo user:", e)

createUser("admin", "123", "admin")

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

for u, r in st:
    createUser(u, "123", r)