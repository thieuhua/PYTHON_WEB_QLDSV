from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse  # Thêm JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .db import models, database
from .routers import mainrouter
from .routers import jwt_auth

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
app.include_router(mainrouter, prefix="/api")

# Mount thư mục static để phục vụ CSS, JS, images
BASE_DIR = Path(__file__).resolve().parent.parent  # thư mục gốc PYTHON_WEB_QLDSV
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend" / "static"), name="static")

# Thiết lập thư mục templates
templates = Jinja2Templates(directory=BASE_DIR / "frontend" / "template")

# ====== MIDDLEWARE FUNCTIONS ======
async def get_current_user(request: Request):
    """Lấy thông tin user từ token"""
    try:
        # Lấy token từ cookie hoặc header
        token = request.cookies.get("token")
        if not token:
            # Hoặc từ Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split("Bearer ")[1]
        
        if token:
            # Sử dụng hàm decode_tokenNE từ jwt_auth
            user = jwt_auth.decode_tokenNE(token)
            return user
    except Exception as e:
        print(f"Auth error: {e}")
    return None

def require_role(required_role: str):
    """Middleware kiểm tra role"""
    async def role_checker(request: Request):
        user = await get_current_user(request)
        
        if not user:
            # Chưa đăng nhập -> chuyển hướng đến login
            return RedirectResponse(url="/login")
        
        # Lấy role thực tế từ database
        from .db import crud
        from .db.database import SessionLocal
        db = SessionLocal()
        try:
            db_user = crud.get_user_by_username(db, user['username'])
            if not db_user or db_user.role != required_role:
                # Không đúng role -> trả về lỗi 403
                raise HTTPException(
                    status_code=403, 
                    detail=f"Yêu cầu role {required_role} để truy cập trang này"
                )
            return db_user
        finally:
            db.close()
    
    return role_checker

# ====== ROUTES WITH MIDDLEWARE ======
@app.get("/", response_class=HTMLResponse)
async def entry(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/student", response_class=HTMLResponse)
async def student_page(request: Request, user = Depends(require_role("student"))):
    return templates.TemplateResponse("studentHome.html", {"request": request})

@app.get("/teacher", response_class=HTMLResponse)
async def teach_page(request: Request, user = Depends(require_role("teacher"))):
    return templates.TemplateResponse("teacherHome.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user = Depends(require_role("admin"))):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/editProfile", response_class=HTMLResponse)
async def edit_profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

# ====== ERROR HANDLER ======
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 403:
        return templates.TemplateResponse("403.html", {"request": request}, status_code=403)
    elif exc.status_code == 401:
        return RedirectResponse(url="/login")
    # For other errors, return JSON response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
 
@app.get("/403", response_class=HTMLResponse)
async def access_denied_page(request: Request):
    return templates.TemplateResponse("403.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")