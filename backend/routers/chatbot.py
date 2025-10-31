from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import database, crud, models
from . import jwt_auth
import requests
from typing import List, Dict, Optional
from datetime import datetime, date

# Import Gemini (nếu có)
try:
    import google.generativeai as genai
    from ..config import GEMINI_API_KEY, USE_GEMINI
    if USE_GEMINI and GEMINI_API_KEY != "YOUR_API_KEY_HERE":
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    GEMINI_AVAILABLE = False
    USE_GEMINI = False

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
        # Đảm bảo không cache dữ liệu cũ
        db.expire_on_commit = True
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
# 🧠 Prompt nền cho AI
# =========================
system_prompt = {
    "role": "system",
    "content": (
        "Bạn là trợ lý AI thân thiện, thông minh và nói tiếng Việt tự nhiên, không dịch word by word. "
        "Phải nói 100% tiếng Việt trong mọi phản hồi. \n\n"
        "Bạn được tích hợp trong hệ thống quản lý sinh viên của trường đại học, "
        "nhưng bạn không bị giới hạn trong lĩnh vực học tập — bạn có thể trò chuyện về công nghệ, thể thao, âm nhạc, khoa học, "
        "tâm lý, kỹ năng sống, và nhiều chủ đề khác như một người bạn hiểu biết và đáng tin cậy.\n\n"
        "Bạn có quyền truy cập vào cơ sở dữ liệu qua các hàm Python (CRUD) để tra cứu thông tin thật.\n\n"
        "Dữ liệu: users, students, teachers, classes, enrollments, teaching_assignments, grades.\n"
        "Nếu câu hỏi không liên quan đến dữ liệu của database thì đừng lôi vào.\n"
        "Trả lời các câu hỏi về điểm số, lớp học, sinh viên, giảng viên từ DB.\n\n"

        "🎯 **Mục tiêu của bạn**:\n"
        "- Phải nói 100% tiếng Việt trong mọi phản hồi. \n"
        "- Giúp sinh viên tìm hiểu, học tập và phát triển bản thân.\n"
        "- Mang đến cảm giác gần gũi, tích cực và dễ chịu trong mọi cuộc trò chuyện.\n"
        "- Giải thích rõ ràng, có logic, và sẵn sàng hỏi lại khi người dùng nói chưa rõ.\n\n"

        "🧠 **Nguyên tắc phản hồi**:\n"
        "• Phải nói 100% tiếng Việt trong mọi phản hồi. \n"
        "• Luôn nói tiếng Việt tự nhiên, thân thiện, có cảm xúc nhẹ nhàng.\n"
        "• **TUYỆT ĐỐI KHÔNG** tự xưng tên model AI (KHÔNG nói 'Ollama', 'Gemini', 'GPT', 'AI'). CHỈ xưng 'mình' hoặc 'tớ'.\n"
        "• Nếu câu hỏi liên quan đến học tập → trả lời ngắn gọn, súc tích, đúng trọng tâm, có thể thêm ví dụ hoặc lời khuyên học hiệu quả.\n"
        "• Nếu câu hỏi ngoài lề → phản hồi linh hoạt, sáng tạo, đưa ví dụ đời thường.\n"
        "• Nếu người dùng nói không rõ → lịch sự hỏi lại.\n"
        "• Nếu không có dữ liệu thật → phản hồi mềm mại như: 'Mình không chắc lắm, nhưng theo mình thì...', hoặc 'Theo hiểu biết chung thì...'.\n"
        "• Khi nói về cảm xúc hoặc cuộc sống → thể hiện đồng cảm, tinh tế.\n"
        "• Khi nói về kiến thức → ưu tiên rõ ràng, logic, thực tế.\n\n"

        "💬 **Phong cách giao tiếp**:\n"
        "- Phải nói 100% tiếng Việt.\n"
        "- Ngôi xưng: 'mình' hoặc 'tớ', gọi người dùng là: 'bạn' hoặc 'cậu'.\n"
        "- **TUYỆT ĐỐI KHÔNG** tự xưng tên model ('Ollama', 'Gemini', 'ChatGPT', 'AI'). CHỈ dùng 'mình' hoặc 'tớ'.\n"
        "- **QUAN TRỌNG**: Khi chào hỏi hoặc xưng hô, LUÔN dùng TÊN THẬT (full_name) của người dùng, KHÔNG dùng username.\n"
        "- Ví dụ: Nếu full_name là 'Nguyễn Văn An', chào 'Xin chào bạn An!' hoặc 'Chào Nguyễn Văn An!', KHÔNG nói 'student1' hay 'user123'.\n"
        "- Thân thiện, tự nhiên, hơi vui hoặc nhẹ nhàng.\n"
        "- Tránh ngôn ngữ cứng nhắc trừ khi cần.\n"
        "- Kết hợp giải thích – ví dụ – lời khuyên – hoặc câu hỏi ngược.\n\n"

        "✨ **Mục tiêu cuối cùng**: "
        "Ngôi xưng 'mình', gọi người dùng là 'bạn'.\n"
        "Sử dụng tiếng Việt 100% tự nhiên (KHÔNG DỊCH WORD BY WORD) để tạo ra trải nghiệm trò chuyện thân thiện. "
        "Người dùng cảm thấy được lắng nghe, được giúp đỡ, "
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
        # CHỈ gửi điểm thành phần (attendance, mid, final) cho AI - BỎ QUA điểm cũ
        all_grades = crud.get_grades_by_student(db, user.user_id)
        component_grades = [g for g in all_grades if g.subject.lower() in ['attendance', 'mid', 'final']]

        profile["grades"] = [
            {
                "class_id": g.class_id,
                "subject": g.subject,
                "score": g.score
            } for g in component_grades
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
# 📊 TÍNH ĐIỂM TRUNG BÌNH CHUẨN
# =========================
def calculate_average(grades: List[models.Grade]) -> float:
    """
    Tính trung bình chung theo công thức:
    - Chuyên cần (Attendance): 20%
    - Giữa kỳ (Mid): 30%
    - Cuối kỳ (Final): 50%

    CHỈ tính các lớp có đầy đủ điểm thành phần (attendance, mid, final)
    Bỏ qua điểm cũ (subject = tên môn học)
    """
    if not grades:
        return 0.0

    # Nhóm điểm theo lớp, CHỈ LẤY điểm thành phần
    component_scores = ['attendance', 'mid', 'final']
    class_grades = {}

    for grade in grades:
        subject_lower = grade.subject.lower()

        # Chỉ lấy 3 loại điểm thành phần, BỎ QUA điểm cũ
        if subject_lower in component_scores:
            if grade.class_id not in class_grades:
                class_grades[grade.class_id] = {}
            class_grades[grade.class_id][subject_lower] = grade.score

    # Tính trung bình từng lớp rồi lấy trung bình chung
    class_averages = []
    for class_id, subjects in class_grades.items():
        attendance = subjects.get('attendance', None)
        mid = subjects.get('mid', None)
        final = subjects.get('final', None)

        # CHỈ tính nếu có ĐẦY ĐỦ 3 điểm thành phần
        if attendance is not None and mid is not None and final is not None:
            weighted_avg = (attendance * 0.2) + (mid * 0.3) + (final * 0.5)
            class_averages.append(weighted_avg)

    if not class_averages:
        return 0.0

    overall_avg = sum(class_averages) / len(class_averages)
    return round(overall_avg, 2)

# =========================
# 📈 PHÂN TÍCH KẾT QUẢ HỌC TẬP CHI TIẾT
# =========================
def analyze_performance(grades: List[models.Grade], db: Session) -> str:
    """
    Phân tích chi tiết kết quả học tập:
    - Nhóm điểm theo loại (Chuyên cần, Giữa kỳ, Cuối kỳ)
    - Tính trung bình từng loại
    - Đưa ra nhận xét và lời khuyên chi tiết
    - CHỈ xử lý điểm thành phần (attendance, mid, final), BỎ QUA điểm cũ
    """
    if not grades:
        return "📝 Bạn chưa có điểm nào trong hệ thống. Hãy học tập chăm chỉ nhé! 💪"

    # --- Chỉ lấy điểm thành phần (attendance, mid, final) ---
    component_grades = [g for g in grades if g.subject.lower() in ['attendance', 'mid', 'final']]

    if not component_grades:
        return "📝 Bạn chưa có điểm thành phần (chuyên cần, giữa kỳ, cuối kỳ) nào. Hãy chờ giáo viên nhập điểm! 📊"

    # --- Nhóm điểm theo loại ---
    score_types = {
        'attendance': [],    # Chuyên cần
        'mid': [],          # Giữa kỳ
        'final': []         # Cuối kỳ
    }

    for grade in component_grades:
        subject = grade.subject.lower()
        if subject in score_types:
            score_types[subject].append(grade.score)

    # --- Tính trung bình từng loại ---
    type_averages = {}
    for score_type, scores in score_types.items():
        if scores:
            type_averages[score_type] = round(sum(scores) / len(scores), 2)

    # --- Tính trung bình chung sử dụng công thức cân nặng ---
    if type_averages:
        attendance_avg = type_averages.get('attendance', 0)
        mid_avg = type_averages.get('mid', 0)
        final_avg = type_averages.get('final', 0)
        overall_avg = round((attendance_avg * 0.2) + (mid_avg * 0.3) + (final_avg * 0.5), 2)
    else:
        overall_avg = 0.0

    # --- Xác định học lực ---
    def get_level(score):
        if score >= 8.5: return "⭐ Xuất sắc"
        elif score >= 7.0: return "✅ Khá"
        elif score >= 5.0: return "📖 Trung bình"
        else: return "⚠️ Yếu"

    # --- Xây dựng phản hồi ---
    analysis = f"📊 **PHÂN TÍCH KẾT QUẢ HỌC TẬP**\n\n"

    # Hiển thị trung bình chung
    analysis += f"🎯 **Điểm trung bình chung: {overall_avg}/10** {get_level(overall_avg)}\n\n"

    # Hiển thị chi tiết từng loại điểm
    analysis += f"📋 **Chi tiết từng thành phần:**\n"
    if 'attendance' in type_averages:
        analysis += f"  • Chuyên cần (20%): {type_averages['attendance']}/10 {get_level(type_averages['attendance'])}\n"
    if 'mid' in type_averages:
        analysis += f"  • Giữa kỳ (30%): {type_averages['mid']}/10 {get_level(type_averages['mid'])}\n"
    if 'final' in type_averages:
        analysis += f"  • Cuối kỳ (50%): {type_averages['final']}/10 {get_level(type_averages['final'])}\n"

    analysis += f"\n"

    # --- Tìm điểm cao nhất và thấp nhất (CHỈ từ component grades) ---
    all_scores = [g.score for g in component_grades if g.score]
    if all_scores:
        highest = max(all_scores)
        lowest = min(all_scores)
        analysis += f"📈 Điểm cao nhất: **{highest}/10**\n"
        analysis += f"📉 Điểm thấp nhất: **{lowest}/10**\n\n"

    # --- Thống kê học lực (CHỈ từ component grades) ---
    analysis += f"📊 **Thống kê học lực:**\n"
    excellent_count = len([s for s in all_scores if s >= 8.5])
    good_count = len([s for s in all_scores if 7.0 <= s < 8.5])
    average_count = len([s for s in all_scores if 5.0 <= s < 7.0])
    weak_count = len([s for s in all_scores if s < 5.0])

    if excellent_count: analysis += f"  ⭐ Xuất sắc (≥8.5): {excellent_count} lần\n"
    if good_count: analysis += f"  ✅ Khá (7.0-8.5): {good_count} lần\n"
    if average_count: analysis += f"  📖 Trung bình (5.0-7.0): {average_count} lần\n"
    if weak_count: analysis += f"  ⚠️ Yếu (<5.0): {weak_count} lần\n"

    analysis += f"\n"

    # --- Nhận xét và lời khuyên ---
    analysis += f"💡 **Nhận xét & Lời khuyên:**\n"

    if overall_avg >= 8.5:
        analysis += "Kết quả **xuất sắc**! Bạn là một học sinh giỏi. Hãy duy trì phong độ này! 🌟\n"
        if 'final' in type_averages and type_averages['final'] < 8.0:
            analysis += "💪 Hãy chú ý hơn vào phần **cuối kỳ** để duy trì mức điểm cao.\n"
    elif overall_avg >= 7.0:
        analysis += "Kết quả **khá tốt**! Bạn đang học tập tốt. Cố gắng thêm một chút nữa để đạt xuất sắc! 💪\n"
        if 'final' in type_averages and type_averages['final'] < type_averages.get('mid', 0):
            analysis += "📚 Để ý: Điểm cuối kỳ của bạn thấp hơn giữa kỳ. Hãy ôn tập kỹ hơn cho kỳ thi cuối!\n"
    elif overall_avg >= 5.0:
        analysis += "Kết quả ở **mức trung bình**. Bạn cần dành nhiều thời gian hơn cho việc học! 📚\n"
        if weak_count > 0:
            analysis += f"⚠️ Bạn có {weak_count} lần điểm dưới 5.0. Hãy tập trung cải thiện các phần này.\n"
        analysis += "💡 Gợi ý: Lập kế hoạch học tập chi tiết, tham gia thêm các buổi ôn tập, hoặc tìm người hướng dẫn.\n"
    else:
        analysis += "Kết quả chưa đạt yêu cầu. Đừng nản chí! 🔥\n"
        analysis += "📌 Bạn cần:\n"
        analysis += "  1. Xác định những môn học gặp khó khăn\n"
        analysis += "  2. Lập lịch học tập khoa học (30-45 phút/lần)\n"
        analysis += "  3. Tìm kiếm sự hỗ trợ từ giáo viên hoặc bạn học\n"
        analysis += "  4. Thực hành thường xuyên để nắm vững kiến thức\n"

    # --- Gợi ý cải thiện ---
    analysis += f"\n🎯 **Gợi ý cải thiện:**\n"
    if 'attendance' in type_averages:
        if type_averages['attendance'] <= overall_avg:
            analysis += f"  • Tăng **chuyên cần**: Dự phòng toàn bộ các buổi học, tham gia tích cực!\n"
    if 'mid' in type_averages:
        if type_averages['mid'] <= overall_avg:
            analysis += f"  • Cải thiện **giữa kỳ**: Ôn tập kỹ lưỡng, làm bài tập mẫu, hỏi giáo viên khi không hiểu.\n"
    if 'final' in type_averages:
        if type_averages['final'] <= overall_avg:
            analysis += f"  • Chuẩn bị **cuối kỳ**: Bắt đầu ôn tập sớm, ghi chép lại kiến thức, làm đề thi mẫu.\n"

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

        # 🔄 QUAN TRỌNG: Xóa cache NGAY để lấy dữ liệu mới nhất từ DB
        db.expire_all()

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

            # CHỈ LẤY điểm thành phần (attendance, mid, final) - ĐỒNG BỘ VỚI ANALYZE
            component_grades = [g for g in grades if g.subject.lower() in ['attendance', 'mid', 'final']]

            if not component_grades:
                return {"response": "📝 Bạn chưa có điểm thành phần nào. Hãy chờ giáo viên nhập điểm! 📊"}

            response = "📊 **ĐIỂM CỦA BẠN (Chi tiết từng thành phần)**\n\n"

            # Nhóm theo lớp
            class_grades = {}
            for grade in component_grades:
                if grade.class_id not in class_grades:
                    cls = crud.get_class(db, grade.class_id)
                    if cls:
                        class_grades[grade.class_id] = {
                            'name': cls.class_name,
                            'attendance': None,
                            'mid': None,
                            'final': None
                        }

                if grade.class_id in class_grades:
                    subject = grade.subject.lower()
                    if subject in ['attendance', 'mid', 'final']:
                        class_grades[grade.class_id][subject] = grade.score

            # Hiển thị từng lớp
            for class_id, data in sorted(class_grades.items()):
                response += f"📚 **{data['name']}**\n"

                if data['attendance'] is not None:
                    response += f"  • Chuyên cần: {data['attendance']}/10\n"
                if data['mid'] is not None:
                    response += f"  • Giữa kỳ: {data['mid']}/10\n"
                if data['final'] is not None:
                    response += f"  • Cuối kỳ: {data['final']}/10\n"

                # Tính điểm trung bình lớp (nếu có đủ 3 thành phần)
                if all(data[k] is not None for k in ['attendance', 'mid', 'final']):
                    avg = (data['attendance'] * 0.2) + (data['mid'] * 0.3) + (data['final'] * 0.5)
                    response += f"  ➜ **Điểm lớp: {avg:.2f}/10**\n"

                response += "\n"

            # Tính điểm trung bình chung
            overall_avg = calculate_average(grades)
            if overall_avg > 0:
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
        
        # Thêm profile người dùng vào context - NÊN BẬT TÊN THẬT
        profile_info = get_user_profile(db, db_user.user_id)
        user_context = (
            f"Người dùng hiện tại:\n"
            f"- Tên: {profile_info.get('full_name', 'N/A')} (DÙNG TÊN NÀY KHI CHÀO)\n"
            f"- Username: {profile_info.get('username', 'N/A')} (ĐỪNG DÙNG USERNAME)\n"
            f"- Vai trò: {profile_info.get('role', 'N/A')}\n"
            f"\nDữ liệu chi tiết: {profile_info}"
        )
        messages.append({
            "role": "user",
            "content": f"{data.message}\n\n[{user_context}]"
        })
        
        # Gọi AI (Gemini hoặc Ollama)
        try:
            if USE_GEMINI and GEMINI_AVAILABLE:
                # ===== SỬ DỤNG GEMINI (Nhanh, chính xác) =====
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')  # Model mới nhất, ổn định

                    # Chuyển đổi messages sang prompt cho Gemini
                    system_text = system_prompt['content']
                    user_text = messages[-1]['content']
                    full_prompt = f"{system_text}\n\n{user_text}"

                    response = model.generate_content(full_prompt)
                    reply = response.text.strip() if response.text else \
                            "Xin lỗi, mình chưa hiểu rõ câu hỏi của bạn. Bạn có thể nói rõ hơn được không? 🤔"

                    return {"response": reply}

                except Exception as gemini_error:
                    # Nếu Gemini lỗi (quota/rate limit), fallback về Ollama
                    print(f"⚠️ Gemini lỗi ({gemini_error}), fallback về Ollama...")
                    # Tiếp tục xuống phần Ollama bên dưới

            # ===== SỬ DỤNG OLLAMA (Local - Fallback) =====
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

        except Exception as e:
            print(f"❌ Lỗi AI: {e}")
            import traceback
            traceback.print_exc()
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
            "📚 Tôi đã đăng ký các lớp học nào",
            "👨‍🏫 Danh sách giảng viên",
            "💡 Làm sao để học hiệu quả hơn?"
        ]}
    except Exception as e:
        print(f"❌ Lỗi suggestions: {e}")
        return {"suggestions": ["📊 Xem điểm", "📚 Xem lớp học", "💡 Tư vấn học tập"]}

