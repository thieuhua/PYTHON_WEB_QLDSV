# Configuration file for AI models
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =========================
# GEMINI API KEY
# =========================
# API key được lưu trong file .env (KHÔNG commit lên Git)
# Để lấy API key miễn phí: https://makersuite.google.com/app/apikey
# Sau đó thêm vào file .env: GEMINI_API_KEY=your_actual_key_here

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not found in .env file!")
    print("📝 Please create .env file and add your API key")
    print("💡 See .env.example for reference")

# =========================
# MODEL SETTINGS
# =========================
USE_GEMINI = os.getenv("USE_GEMINI", "True").lower() == "true"

# Nếu muốn dùng lại Ollama, đổi USE_GEMINI = False trong file .env
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")  # hoặc "mistral", "phi3"

