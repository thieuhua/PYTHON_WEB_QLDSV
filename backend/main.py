from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
# from . import models, database
from .routers import items

# models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
app.include_router(items.router)

# Mount thư mục static để phục vụ CSS, JS, images
BASE_DIR = Path(__file__).resolve().parent.parent  # thư mục gốc PYTHON_WEB_QLDSV
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend" / "static"), name="static")

# Thiết lập thư mục templates
templates = Jinja2Templates(directory=BASE_DIR / "frontend" / "template")

# Route gốc trả về HTML
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")