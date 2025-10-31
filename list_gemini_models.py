"""List available Gemini models"""
import google.generativeai as genai
from backend.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

print("📋 DANH SÁCH CÁC MODEL GEMINI KHẢ DỤNG:\n")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Hỗ trợ: {', '.join(model.supported_generation_methods)}")
        print()

