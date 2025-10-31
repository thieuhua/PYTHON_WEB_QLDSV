# Configuration file for AI models

# =========================
# GEMINI API KEY
# =========================
# Lấy API key miễn phí tại: https://makersuite.google.com/app/apikey
# Sau khi lấy được, thay "YOUR_API_KEY_HERE" bằng API key thật

GEMINI_API_KEY = "AIzaSyBnKlbs1VW5EqmnaURssOIWbJ-Azrs6PxM"  # ← THAY ĐỔI CHỖ NÀY

# =========================
# MODEL SETTINGS
# =========================
USE_GEMINI = True  # Đổi thành True khi đã có API key

# Nếu muốn dùng lại Ollama, đổi USE_GEMINI = False
OLLAMA_MODEL = "llama3"  # hoặc "mistral", "phi3"

