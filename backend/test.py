# file: main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# Route gốc trả về chuỗi HTML
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head>
            <title>FastAPI Localhost Example</title>
        </head>
        <body>
            <h1>Xin chào từ FastAPI!</h1>
            <p>Trang web đang chạy trên localhost.</p>
        </body>
    </html>
    """

# Một route API trả về JSON
@app.get("/api/hello")
async def say_hello():
    return {"message": "Hello, FastAPI!"}

if __name__ == "__main__":
    import uvicorn
    # Chạy server tại 127.0.0.1:8000
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
