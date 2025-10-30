from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import anthropic
import os
from datetime import datetime

from ..db import crud, models, database
from . import jwt_auth

router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"]
)

# Khởi tạo Anthropic client
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# Models
class ChatMessage(BaseModel):
    role: str  # "user" hoặc "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    timestamp: str

# Helper function để lấy context về sinh viên
def get_student_context(db: Session, user_id: int) -> str:
    """Lấy thông tin sinh viên để cung cấp context cho chatbot"""
    user = crud.get_user(db, user_id)
    if not user or not user.student_profile:
        return ""
    
    context_parts = [
        f"Thông tin sinh viên:",
        f"- Họ tên: {user.full_name}",
        f"- Mã sinh viên: {user.student_profile.student_code}",
    ]
    
    if user.student_profile.birthdate:
        context_parts.append(f"- Ngày sinh: {user.student_profile.birthdate}")
    
    # Lấy danh sách lớp đang học
    enrollments = crud.get_student_enrollments(db, user.user_id)
    if enrollments:
        context_parts.append(f"\nĐang học {len(enrollments)} lớp:")
        for enrollment in enrollments:
            cls = crud.get_class(db, enrollment.class_id)
            if cls:
                context_parts.append(f"  - {cls.class_name} (Năm {cls.year}, HK{cls.semester})")
    
    # Lấy điểm số
    grades = crud.get_student_grades(db, user.user_id)
    if grades:
        context_parts.append(f"\nĐiểm số gần đây:")
        # Nhóm điểm theo lớp
        grades_by_class = {}
        for grade in grades:
            if grade.class_id not in grades_by_class:
                grades_by_class[grade.class_id] = []
            grades_by_class[grade.class_id].append(grade)
        
        for class_id, class_grades in grades_by_class.items():
            cls = crud.get_class(db, class_id)
            if cls:
                context_parts.append(f"  Lớp {cls.class_name}:")
                for grade in class_grades:
                    context_parts.append(f"    - {grade.subject}: {grade.score}")
    
    return "\n".join(context_parts)

def get_system_prompt(student_context: str) -> str:
    """Tạo system prompt cho chatbot"""
    return f"""Bạn là một trợ lý AI thông minh và thân thiện, được thiết kế để tư vấn và hỗ trợ sinh viên.

{student_context}

Nhiệm vụ của bạn:
1. Trả lời các câu hỏi về học tập, điểm số, lịch học
2. Tư vấn về việc cải thiện kết quả học tập
3. Giải đáp thắc mắc về quy định, quy trình của trường
4. Động viên và khuyến khích sinh viên
5. Đưa ra lời khuyên xây dựng về việc học và phát triển bản thân

Phong cách giao tiếp:
- Thân thiện, gần gũi nhưng chuyên nghiệp
- Sử dụng tiếng Việt tự nhiên
- Ngắn gọn, súc tích nhưng đầy đủ thông tin
- Động viên tích cực
- Nếu không biết, hãy thành thật thừa nhận và gợi ý liên hệ với giáo viên/ban quản lý

Lưu ý:
- KHÔNG bịa đặt thông tin không có trong dữ liệu
- Sử dụng thông tin sinh viên ở trên để cá nhân hóa câu trả lời
- Nếu sinh viên hỏi về điểm, hãy phân tích và đưa ra lời khuyên cụ thể
"""

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(jwt_auth.auth),
    db: Session = Depends(database.get_db)
):
    """
    API endpoint cho chatbot AI tư vấn sinh viên
    """
    try:
        # Lấy context về sinh viên
        student_context = get_student_context(db, current_user.get('id'))
        system_prompt = get_system_prompt(student_context)
        
        # Chuẩn bị conversation history
        messages = []
        
        # Thêm lịch sử hội thoại nếu có
        for msg in request.conversation_history[-10:]:  # Chỉ lấy 10 tin nhắn gần nhất
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Thêm tin nhắn hiện tại
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Gọi Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )
        
        # Lấy nội dung response
        assistant_message = response.content[0].text
        
        return ChatResponse(
            response=assistant_message,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"Chatbot error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi khi xử lý chatbot: {str(e)}"
        )

@router.get("/suggestions")
async def get_suggestions(
    current_user: dict = Depends(jwt_auth.auth),
    db: Session = Depends(database.get_db)
):
    """
    Lấy danh sách câu hỏi gợi ý cho sinh viên
    """
    suggestions = [
        "Điểm của em trong các môn học như thế nào?",
        "Em nên làm gì để cải thiện điểm số?",
        "Cho em xem lịch học của em",
        "Em đang học những môn gì?",
        "Tính điểm trung bình của em",
        "Tư vấn cho em về việc học tập hiệu quả",
        "Làm thế nào để quản lý thời gian học tốt hơn?",
        "Em cần chuẩn bị gì cho kỳ thi cuối kỳ?"
    ]
    
    return {"suggestions": suggestions}

@router.post("/feedback")
async def submit_feedback(
    feedback: dict,
    current_user: dict = Depends(jwt_auth.auth)
):
    """
    Nhận phản hồi về chất lượng chatbot
    """
    # TODO: Lưu feedback vào database
    print(f"Feedback from user {current_user.get('username')}: {feedback}")
    
    return {
        "message": "Cảm ơn bạn đã đóng góp ý kiến!",
        "status": "success"
    }