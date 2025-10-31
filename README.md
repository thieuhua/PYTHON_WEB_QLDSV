# PYTHON_WEB_QLDSV
web quản lý điểm sinh viên



cấu hình:
my_project/
│── backend/
│   ├── main.py              # entry point của FastAPI
│   ├── database.py          # cấu hình DB
│   ├── models.py            # ORM models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # các hàm thao tác DB
│   └── routers/
│       └── items.py         # router (API) ví dụ
│
│── frontend/
│   └── template/
|       └── index.html           
│   └── static/
|       └── stript.js
|       └── styles.css
│
│── requirements.txt         # thư viện cần cài

nếu muốn chạy chatbot:
tải ở https://ollama.com/download
tiếp đó pip install ollama
mở CMD ollama serve
ollama pull llama3:instruct

chạy:
# tạo virtual env nếu muốn
pip install -r requirements.txt
uvicorn backend.main:app --reload

