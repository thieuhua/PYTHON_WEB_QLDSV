from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import database, crud
from . import jwt_auth
import requests

router = APIRouter(
    prefix="/api/chatbot",
    tags=["Chatbot"]
)

# ✅ Kết nối DB
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 🧠 Schema message từ frontend
class ChatMessage(BaseModel):
    message: str
    conversation_history: list | None = None

# 🧠 Prompt nền cho AI
system_prompt = {
    "role": "system",
    "content": (
        "Bạn là Ollama — một trợ lý AI thân thiện, thông minh và nói tiếng Việt tự nhiên, không dịch word by word. "
        "Phải nói 100% tiếng Việt trong mọi phản hồi. \n\n"
        "Bạn được tích hợp trong hệ thống quản lý sinh viên của trường đại học, "
        "nhưng bạn không bị giới hạn trong lĩnh vực học tập — bạn có thể trò chuyện về công nghệ, thể thao, âm nhạc, khoa học, "
        "Bạn có quyền truy cập vào cơ sở dữ liệu qua các hàm Python (CRUD) để tra cứu thông tin thật.\n\n"
        "Dữ liệu: users, students, teachers, classes, enrollments, teaching_assignments, grades.\n"
        "Trả lời các câu hỏi về điểm số, lớp học, sinh viên, giảng viên từ DB.\n"
        "tâm lý, kỹ năng sống, và nhiều chủ đề khác như một người bạn hiểu biết và đáng tin cậy.\n\n"

        "🎯 **Mục tiêu của bạn**:\n"
        "- Giúp sinh viên tìm hiểu, học tập và phát triển bản thân.\n"
        "- Mang đến cảm giác gần gũi, tích cực và dễ chịu trong mọi cuộc trò chuyện.\n"
        "- Giải thích rõ ràng, có logic, và sẵn sàng hỏi lại khi người dùng nói chưa rõ.\n\n"

        "🧠 **Nguyên tắc phản hồi**:\n"
        "• Luôn nói tiếng Việt tự nhiên, thân thiện, có cảm xúc nhẹ nhàng như đang nói chuyện trực tiếp.\n"
        "• Nếu câu hỏi liên quan đến học tập → trả lời ngắn gọn, súc tích, đúng trọng tâm, có thể thêm ví dụ hoặc lời khuyên học hiệu quả.\n"
        "• Nếu câu hỏi ngoài lề → phản hồi linh hoạt, sáng tạo, có thể đưa quan điểm hoặc ví dụ đời thường để tạo cảm giác thật.\n"
        "• Nếu người dùng nói không rõ → lịch sự hỏi lại để làm rõ trước khi trả lời.\n"
        "• Nếu không có dữ liệu thật → phản hồi mềm mại, như: 'Mình không chắc lắm, nhưng theo mình thì...', hoặc 'Theo hiểu biết chung thì...'.\n"
        "• Khi nói về cảm xúc hoặc cuộc sống → thể hiện sự đồng cảm, tinh tế, không rập khuôn.\n"
        "• Khi nói về kiến thức → ưu tiên sự rõ ràng, logic, và có tính thực tế.\n\n"

        "💬 **Phong cách giao tiếp**:\n"
        "- Dùng ngôi xưng “mình” khi nói, và gọi người dùng là “bạn”.\n"
        "- Giọng điệu thân thiện, tự nhiên, có thể hơi vui hoặc nhẹ nhàng tùy tình huống.\n"
        "- Tránh dùng ngôn ngữ cứng nhắc hoặc quá học thuật trừ khi người dùng yêu cầu.\n"
        "- Có thể kết hợp giải thích – ví dụ – lời khuyên – hoặc câu hỏi ngược để tương tác tự nhiên.\n\n"

        "✨ **Mục tiêu cuối cùng**: "
        "Khi trò chuyện với Ollama, người dùng cảm thấy được lắng nghe, được giúp đỡ, "
        "và có thể nói chuyện thoải mái như với một người bạn thông minh, tích cực và luôn sẵn lòng hỗ trợ."
    )
}



# 💬 API chính: chat với AI
@router.post("/chat")
async def chat_with_ai(
    data: ChatMessage,
    db: Session = Depends(get_db),
    current_user=Depends(jwt_auth.get_current_user)
):
    try:
        messages = [system_prompt]
        if data.conversation_history:
            messages.extend(data.conversation_history)
        messages.append({"role": "user", "content": data.message})

        user_message = data.message.lower().strip()

        # ------------------------
        # Truy vấn dữ liệu thật từ DB
        # ------------------------
        if "điểm" in user_message or "gpa" in user_message:
            grades = crud.get_grades_by_student(db, current_user.user_id)
            if not grades:
                return {"response": "Hiện bạn chưa có điểm nào được lưu trong hệ thống nha!"}
            formatted = "\n".join([f"- {g.subject}: {g.score}" for g in grades])
            return {"response": f"📊 Điểm của bạn trong hệ thống:\n{formatted}"}

        elif "lớp" in user_message and "đăng ký" in user_message:
            enrollments = crud.get_student_enrollments(db, current_user.user_id)
            if not enrollments:
                return {"response": "Bạn chưa đăng ký lớp học nào trong hệ thống nha!"}
            class_names = []
            for e in enrollments:
                cls = crud.get_class(db, e.class_id)
                if cls:
                    class_names.append(f"- {cls.class_name} (Học kỳ {cls.semester}/{cls.year})")
            return {"response": f"📚 Bạn đang theo học các lớp sau:\n" + "\n".join(class_names)}

        elif "giảng viên" in user_message or "teacher" in user_message:
            teachers = crud.get_teachers(db)
            if not teachers:
                return {"response": "Hiện hệ thống chưa có giảng viên nào."}
            formatted = "\n".join([f"- {t.user.full_name} ({t.title or 'Giảng viên'})" for t in teachers])
            return {"response": f"👩‍🏫 Danh sách giảng viên hiện có:\n{formatted}"}

        # ------------------------
        # Nếu không match → gửi AI
        # ------------------------
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3",
                "messages": messages,
                "stream": False
            },
            timeout=60
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Không thể kết nối tới Ollama")

        result = response.json()
        reply = result.get("message", {}).get("content", "").strip()
        if not reply:
            reply = "Xin lỗi, mình chưa có thông tin cụ thể về câu này, bạn có thể nói rõ hơn không?"
        return {"response": reply}

    except Exception as e:
        print("❌ Lỗi chatbot:", e)
        raise HTTPException(status_code=500, detail="Đã có lỗi xảy ra khi xử lý yêu cầu.")

# 💡 Gợi ý câu hỏi
@router.get("/suggestions")
async def get_chatbot_suggestions(current_user=Depends(jwt_auth.get_current_user)):
    return {
        "suggestions": [
            "📊 Xem điểm của tôi trong học kỳ này",
            "📚 Tôi đang học những lớp nào?",
            "👩‍🏫 Danh sách giảng viên trong trường là ai?",
            "🎵 Gợi ý vài bài nhạc giúp tôi học tập trung hơn",
            "⚽ Bạn có thích bóng đá không?",
            "🤖 AI có thể thay thế con người trong tương lai không?"
        ]
    }
