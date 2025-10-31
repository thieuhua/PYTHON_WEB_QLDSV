from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import database, crud, models
from . import jwt_auth
import requests
from typing import List, Dict, Optional
from datetime import datetime, date

router = APIRouter(
    prefix="/api/chatbot",
    tags=["Chatbot"]
)

# =========================
# ✅ Kết nối DB
# =========================
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# 🧠 Schema message từ frontend
# =========================
class ChatMessage(BaseModel):
    message: str
    conversation_history: List[Dict[str, str]] | None = None

# =========================
# 🧠 Prompt nền cho AI - NGUYÊN VẸN
# =========================
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
        "- Phải nói 100% tiếng Việt trong mọi phản hồi. \n"
        "- Giúp sinh viên tìm hiểu, học tập và phát triển bản thân.\n"
        "- Mang đến cảm giác gần gũi, tích cực và dễ chịu trong mọi cuộc trò chuyện.\n"
        "- Giải thích rõ ràng, có logic, và sẵn sàng hỏi lại khi người dùng nói chưa rõ.\n\n"

        "🧠 **Nguyên tắc phản hồi**:\n"
        "• Phải nói 100% tiếng Việt trong mọi phản hồi. \n"
        "• Luôn nói tiếng Việt tự nhiên, thân thiện, có cảm xúc nhẹ nhàng.\n"
        "• Nếu câu hỏi liên quan đến học tập → trả lời ngắn gọn, súc tích, đúng trọng tâm, có thể thêm ví dụ hoặc lời khuyên học hiệu quả.\n"
        "• Nếu câu hỏi ngoài lề → phản hồi linh hoạt, sáng tạo, đưa ví dụ đời thường.\n"
        "• Nếu người dùng nói không rõ → lịch sự hỏi lại.\n"
        "• Nếu không có dữ liệu thật → phản hồi mềm mại như: 'Mình không chắc lắm, nhưng theo mình thì...', hoặc 'Theo hiểu biết chung thì...'.\n"
        "• Khi nói về cảm xúc hoặc cuộc sống → thể hiện đồng cảm, tinh tế.\n"
        "• Khi nói về kiến thức → ưu tiên rõ ràng, logic, thực tế.\n\n"

        "💬 **Phong cách giao tiếp**:\n"
        "- Phải nói 100% tiếng Việt.\n"
        "- Ngôi xưng “mình”, gọi người dùng là “bạn”.\n"
        "- Thân thiện, tự nhiên, hơi vui hoặc nhẹ nhàng.\n"
        "- Tránh ngôn ngữ cứng nhắc trừ khi cần.\n"
        "- Kết hợp giải thích – ví dụ – lời khuyên – hoặc câu hỏi ngược.\n\n"

        "✨ **Mục tiêu cuối cùng**: "
        "Khi trò chuyện với Ollama, người dùng cảm thấy được lắng nghe, được giúp đỡ, "
        "và có thể nói chuyện thoải mái như với một người bạn thông minh, tích cực và luôn sẵn lòng hỗ trợ."
    )
}

# =========================
# 🔍 HÀM HỖ TRỢ - PHÂN TÍCH CÂU HỎI
# =========================
def analyze_question(message: str) -> Dict[str, bool]:
    msg = message.lower().strip()
    return {
        "want_grades": any(word in msg for word in ["điểm", "score", "gpa", "grade"]),
        "want_classes": any(word in msg for word in ["lớp", "class", "môn học", "subject", "đăng ký"]),
        "want_schedule": any(word in msg for word in ["lịch", "schedule", "thời khóa biểu"]),
        "want_stats": any(word in msg for word in ["thống kê", "trung bình", "cao nhất", "thấp nhất", "stats", "average"]),
        "want_analysis": any(word in msg for word in ["phân tích", "đánh giá", "nhận xét", "analyze"])
    }

# =========================
# ✅ LẤY PROFILE NGƯỜI DÙNG
# =========================
def get_user_profile(db: Session, user_id: int) -> Dict:
    """Trả về thông tin user kèm profile sinh viên/giảng viên nếu có"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user")
    
    profile = {
        "user_id": user.user_id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role)
    }

    if user.role == models.UserRole.student and user.student_profile:
        profile["student_profile"] = {
            "student_id": user.student_profile.student_id,
            "student_code": user.student_profile.student_code,
            "birthdate": user.student_profile.birthdate
        }
        profile["enrollments"] = [
            {
                "class_id": e.class_id,
                "class_name": crud.get_class(db, e.class_id).class_name if crud.get_class(db, e.class_id) else None,
                "enroll_date": e.enroll_date
            } for e in crud.get_student_enrollments(db, user.user_id)
        ]
        profile["grades"] = [
            {
                "class_id": g.class_id,
                "subject": g.subject,
                "score": g.score
            } for g in crud.get_grades_by_student(db, user.user_id)
        ]
    
    elif user.role == models.UserRole.teacher and user.teacher_profile:
        profile["teacher_profile"] = {
            "teacher_id": user.teacher_profile.teacher_id,
            "department": user.teacher_profile.department,
            "title": user.teacher_profile.title
        }
        profile["assignments"] = [
            {
                "class_id": a.class_id,
                "class_name": crud.get_class(db, a.class_id).class_name if crud.get_class(db, a.class_id) else None
            } for a in db.query(models.TeachingAssignment).filter(models.TeachingAssignment.teacher_id==user.user_id).all()
        ]

    return profile

# =========================
# 📊 TÍNH ĐIỂM TRUNG BÌNH
# =========================
def calculate_average(grades: List[models.Grade]) -> float:
    if not grades:
        return 0.0
    class_grades = {}
    for grade in grades:
        if grade.class_id not in class_grades:
            class_grades[grade.class_id] = {}
        class_grades[grade.class_id][grade.subject.lower()] = grade.score
    total_avg = 0
    count = 0
    for subjects in class_grades.values():
        Chuyên_cần = subjects.get('attendance', 0)
        Giữa_kì = subjects.get('mid', 0)
        Cuối_kì = subjects.get('final', 0)
        if Chuyên_cần or Giữa_kì or Cuối_kì:
            weighted_avg = (Chuyên_cần * 0.2) + (Giữa_kì * 0.3) + (Cuối_kì * 0.5)
            total_avg += weighted_avg
            count += 1
    return round(total_avg / count, 2) if count else 0.0

# =========================
# 📈 PHÂN TÍCH KẾT QUẢ HỌC TẬP
# =========================
def analyze_performance(grades: List[models.Grade], db: Session) -> str:
    if not grades:
        return "Bạn chưa có điểm nào trong hệ thống. Hãy học tập chăm chỉ nhé! 💪"

    # --- Nhóm điểm theo môn ---
    subject_scores = {}
    for g in grades:
        s = g.score or 0
        # dùng subject làm key
        if g.subject not in subject_scores:
            subject_scores[g.subject] = []
        subject_scores[g.subject].append(s)

    # --- Trung bình mỗi môn ---
    subject_avg = {sub: round(sum(scores)/len(scores), 2) for sub, scores in subject_scores.items()}

    # --- Tổng hợp phân tích ---
    scores_avg = list(subject_avg.values())
    overall_avg = round(sum(scores_avg)/len(scores_avg), 2)
    highest = max(scores_avg)
    lowest = min(scores_avg)

    # Phân bố điểm
    excellent = len([s for s in scores_avg if s >= 8.5])
    good = len([s for s in scores_avg if 7.0 <= s < 8.5])
    average = len([s for s in scores_avg if 5.0 <= s < 7.0])
    weak = len([s for s in scores_avg if s < 5.0])

    analysis = f"📊 **PHÂN TÍCH KẾT QUẢ HỌC TẬP**\n\n"
    analysis += f"📌 Tổng số môn: {len(subject_avg)}\n"
    analysis += f"🎯 Điểm trung bình chung: **{overall_avg}/10**\n"
    analysis += f"🏆 Điểm cao nhất: **{highest}/10**\n"
    analysis += f"📉 Điểm thấp nhất: **{lowest}/10**\n\n"

    analysis += f"📚 **Chi tiết từng môn:**\n"
    for sub, avg_score in subject_avg.items():
        analysis += f"• {sub}: Trung bình {avg_score}/10\n"

    analysis += f"\n📈 **Phân bố điểm:**\n"
    if excellent: analysis += f"  ⭐ Xuất sắc (≥8.5): {excellent} môn\n"
    if good:      analysis += f"  ✅ Khá (7.0-8.5): {good} môn\n"
    if average:   analysis += f"  📖 Trung bình (5.0-7.0): {average} môn\n"
    if weak:      analysis += f"  ⚠️ Yếu (<5.0): {weak} môn\n"

    analysis += f"\n💡 **Nhận xét:**\n"
    if overall_avg >= 8.5:
        analysis += "Kết quả xuất sắc! Hãy duy trì phong độ này! 🌟"
    elif overall_avg >= 7.0:
        analysis += "Kết quả khá tốt! Hãy cố gắng thêm một chút để đạt điểm cao hơn! 💪"
    elif overall_avg >= 5.0:
        analysis += "Kết quả ở mức trung bình. Bạn nên dành nhiều thời gian hơn cho việc học! 📚"
    else:
        analysis += "Kết quả chưa tốt. Đừng nản chí, hãy tìm phương pháp học phù hợp và cố gắng hơn nữa! 🔥"

    if weak:
        analysis += f"\n⚠️ Bạn có {weak} môn cần cải thiện. Hãy tập trung vào những môn này!"

    return analysis





# =========================
# 💬 API chính: chat với AI
# =========================
@router.post("/chat")
async def chat_with_ai(
    data: ChatMessage,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        token = request.cookies.get("access_token") or \
                (request.headers.get("Authorization").split("Bearer ")[1] 
                 if request.headers.get("Authorization", "").startswith("Bearer ") else None)
        
        if not token:
            raise HTTPException(status_code=401, detail="Chưa đăng nhập")
        
        user_data = jwt_auth.decode_tokenNE(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
        
        username = user_data.get('username')
        user_id = user_data.get('id')
        db_user = crud.get_user_by_username(db, username)
        if not db_user:
            raise HTTPException(status_code=404, detail="Không tìm thấy user")
        
        student_id = db_user.student_profile.student_id if db_user.role==models.UserRole.student and db_user.student_profile else None
        
        intent = analyze_question(data.message)
        user_message = data.message.lower().strip()
        
        # --- Xử lý yêu cầu điểm ---
        if intent["want_grades"] and student_id:
            grades = crud.get_grades_by_student(db, student_id)
            if not grades:
                return {"response": "📝 Bạn chưa có điểm nào trong hệ thống. Hãy chăm chỉ học tập nhé! 💪"}
            
            class_grades = {}
            for grade in grades:
                cls = crud.get_class(db, grade.class_id)
                if cls:
                    cname = cls.class_name
                    if cname not in class_grades:
                        class_grades[cname] = {}
                    class_grades[cname][grade.subject] = grade.score
            
            response = "📊 **ĐIỂM CỦA BẠN**\n\n"
            for cname, subjects in class_grades.items():
                response += f"📚 **{cname}**\n"
                for sub, s in subjects.items():
                    response += f"  • {sub}: {s}/10\n"
                scores = list(subjects.values())
                avg = sum(scores)/len(scores) if scores else 0
                response += f"  ➜ **Trung bình: {avg:.2f}/10**\n\n"
            
            overall_avg = calculate_average(grades)
            response += f"🎯 **Điểm trung bình chung: {overall_avg}/10**"
            return {"response": response}
        
        # --- Xử lý lớp học ---
        elif intent["want_classes"] and student_id:
            enrollments = crud.get_student_enrollments(db, student_id)
            if not enrollments:
                return {"response": "📚 Bạn chưa đăng ký lớp học nào. Hãy đăng ký để bắt đầu học tập nhé! 🎓"}
            
            response = "📚 **CÁC LỚP HỌC CỦA BẠN**\n\n"
            for e in enrollments:
                cls = crud.get_class(db, e.class_id)
                if cls:
                    assign = db.query(models.TeachingAssignment).filter(models.TeachingAssignment.class_id==cls.class_id).first()
                    teacher_name = "Chưa phân công"
                    if assign:
                        t = crud.get_teacher(db, assign.teacher_id)
                        if t and t.user: teacher_name = t.user.full_name
                    response += f"🎓 {cls.class_name}\n  • Năm học: {cls.year}\n  • Học kỳ: {cls.semester}\n  • Giảng viên: {teacher_name}\n  • Ngày đăng ký: {e.enroll_date}\n\n"
            return {"response": response}
        
        # --- Phân tích kết quả ---
        elif (intent["want_stats"] or intent["want_analysis"]) and student_id:
            grades = crud.get_grades_by_student(db, student_id)
            analysis = analyze_performance(grades, db)
            return {"response": analysis}
        
        # --- Danh sách giảng viên ---
        elif "giảng viên" in user_message or "teacher" in user_message:
            teachers = crud.get_teachers(db)
            if not teachers:
                return {"response": "Hiện hệ thống chưa có giảng viên nào."}
            response = "👨‍🏫 **DANH SÁCH GIẢNG VIÊN**\n\n"
            for t in teachers:
                if t.user:
                    response += f"• {t.user.full_name}\n"
                    if t.title: response += f"  Chức danh: {t.title}\n"
                    if t.department: response += f"  Khoa: {t.department}\n"
                    response += "\n"
            return {"response": response}
        
        # --- Gửi câu hỏi không xác định cho AI ---
        messages = [system_prompt]
        if data.conversation_history:
            messages.extend(data.conversation_history)
        
        # Thêm profile người dùng vào context
        profile_info = get_user_profile(db, db_user.user_id)
        messages.append({
            "role": "user",
            "content": f"{data.message}\n[Thông tin người dùng: {profile_info}]"
        })
        
        # Gọi Ollama
        try:
            res = requests.post(
                "http://localhost:11434/api/chat",
                json={"model":"llama3","messages":messages,"stream":False},
                timeout=60
            )
            if res.status_code != 200:
                return {"response": "⚠️ Không thể kết nối tới AI. Vui lòng thử lại sau!"}
            result = res.json()
            reply = result.get("message", {}).get("content", "").strip() or \
                    "Xin lỗi, mình chưa hiểu rõ câu hỏi của bạn. Bạn có thể nói rõ hơn được không? 🤔"
            return {"response": reply}
        except requests.exceptions.RequestException:
            return {"response": "🤖 AI đang bận, nhưng mình vẫn có thể giúp bạn:\n\n• Xem điểm\n• Thống kê kết quả học tập\n• Danh sách giảng viên\n\nBạn muốn biết điều gì? 😊"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Lỗi chatbot: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Đã có lỗi xảy ra khi xử lý yêu cầu.")

# =========================
# 💡 GỢI Ý CÂU HỎI
# =========================
@router.get("/suggestions")
async def get_chatbot_suggestions(request: Request):
    try:
        token = request.cookies.get("access_token") or \
                (request.headers.get("Authorization").split("Bearer ")[1] 
                 if request.headers.get("Authorization", "").startswith("Bearer ") else None)
        if not token:
            return {"suggestions": ["🤖 Chatbot này có thể làm gì?", "📚 Hướng dẫn sử dụng hệ thống", "💡 Tips học tập hiệu quả"]}
        
        user_data = jwt_auth.decode_tokenNE(token)
        if not user_data:
            return {"suggestions": ["🤖 Chatbot có thể giúp gì cho bạn?"]}
        
        return {"suggestions": [
            "📊 Xem điểm của tôi",            
            "📈 Phân tích kết quả học tập của tôi",
            "👨‍🏫 Tôi đã đăng ký các lớp học nào",
            "💡 Làm sao để học hiệu quả hơn?",
            "👨‍🏫 Danh sách giảng viên",
            "🎯 Tính điểm trung bình của tôi"
        ]}
    except Exception as e:
        print(f"❌ Lỗi suggestions: {e}")
        return {"suggestions": ["📊 Xem điểm", "📚 Xem lớp học", "💡 Tư vấn học tập"]}
