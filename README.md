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

<!-- nếu muốn chạy chatbot:
tải ở https://ollama.com/download
tiếp đó pip install ollama
mở CMD ollama serve
ollama pull llama3:instruct -->

chạy:
# 1. Tạo virtual env (khuyến nghị)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. 🔒 QUAN TRỌNG: Thiết lập biến môi trường
# Copy file mẫu
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Sau đó mở file .env và thêm API key thật của bạn:
# GEMINI_API_KEY=your_actual_api_key_here

# 4. Chạy server
uvicorn backend.main:app --reload

---

## 🔒 BẢO MẬT

⚠️ **QUAN TRỌNG**: File `.env` chứa API keys và secrets - **KHÔNG BAO GIỜ** commit lên Git!

### Quick Setup:
1. Copy `.env.example` thành `.env`
2. Lấy Gemini API key tại: https://makersuite.google.com/app/apikey
3. Thêm key vào file `.env`
4. Tạo JWT secret: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

📖 Xem chi tiết: [SECURITY.md](SECURITY.md)


