// ===== CẤU HÌNH API =====
const API_BASE_URL = 'http://127.0.0.1:8000/api'; // THAY ĐỔI URL NÀY NẾU CẦN

let scoreChart = null;
let currentUser = null;

// ===== Lấy headers với token =====
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// ===== Hiển thị thông báo =====
function showNotification(message, isError = false) {
    const notif = document.createElement('div');
    notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${isError ? '#f44336' : '#4CAF50'};
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        font-size: 14px;
        max-width: 300px;
    `;
    notif.textContent = message;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notif.remove(), 300);
    }, 3500);
}

// ===== 1. LẤY THÔNG TIN SINH VIÊN HIỆN TẠI =====
async function fetchCurrentUser() {
    try {
        const response = await fetch(`/api/me`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Không thể lấy thông tin người dùng');
        }
        
        const data = await response.json();
        console.log('✅ User data:', data);
        currentUser = data;
        renderStudentInfo(data);
        return data;
    } catch (error) {
        console.error('❌ Error fetching user:', error);
        showNotification('Không thể tải thông tin sinh viên', true);
        return null;
    }
}

// ===== 2. HIỂN THỊ THÔNG TIN SINH VIÊN =====
function renderStudentInfo(userData) {
    // Họ tên
    document.getElementById('student-name').textContent = userData.full_name || 'N/A';
    
    // Nếu là sinh viên
    if (userData.role === 'student' && userData.student_profile) {
        const profile = userData.student_profile;
        
        document.getElementById('student-id').textContent = profile.student_code || 'N/A';
        
        // Format ngày sinh từ "2002-12-12" -> "12/12/2002"
        if (profile.birthdate) {
            const date = new Date(profile.birthdate);
            const formatted = `${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}/${date.getFullYear()}`;
            document.getElementById('birth-date').textContent = formatted;
        } else {
            document.getElementById('birth-date').textContent = 'N/A';
        }
        
        document.getElementById('student-class').textContent = 'Sinh viên';
    } 
    
}

// ===== 3. LẤY DANH SÁCH LỚP HỌC =====
async function fetchStudentClasses(studentId) {
    try {
        console.log(`📡 Fetching enrollments for student ${studentId}...`);
        
        // Lấy danh sách enrollment
        const enrollResponse = await fetch(`${API_BASE_URL}/students/${studentId}/enrollments`, {
            headers: getAuthHeaders()
        });
        
        if (!enrollResponse.ok) {
            throw new Error('Không thể lấy danh sách lớp học');
        }
        
        const enrollments = await enrollResponse.json();
        console.log('📚 Enrollments:', enrollments);
        
        if (enrollments.length === 0) {
            return [];
        }
        
        // Lấy thông tin chi tiết của từng lớp
        const classesPromises = enrollments.map(async (enrollment) => {
            try {
                const classResponse = await fetch(`${API_BASE_URL}/classes/${enrollment.class_id}`, {
                    headers: getAuthHeaders()
                });
                
                if (classResponse.ok) {
                    return await classResponse.json();
                }
                return null;
            } catch (error) {
                console.error(`Error fetching class ${enrollment.class_id}:`, error);
                return null;
            }
        });
        
        const classes = await Promise.all(classesPromises);
        const validClasses = classes.filter(cls => cls !== null);
        
        console.log('✅ Classes loaded:', validClasses);
        return validClasses;
        
    } catch (error) {
        console.error('❌ Error fetching classes:', error);
        showNotification('Không thể tải danh sách lớp học', true);
        return [];
    }
}

// ===== 4. HIỂN THỊ DANH SÁCH LỚP HỌC =====
async function generateClassCards() {
    const grid = document.getElementById('classes-grid');
    grid.innerHTML = '<div style="text-align:center;padding:40px;color:#666;">⏳ Đang tải danh sách lớp học...</div>';
    
    try {
        // Lấy thông tin user
        if (!currentUser) {
            const user = await fetchCurrentUser();
            if (!user) {
                grid.innerHTML = '<div style="text-align:center;padding:40px;color:#f44336;">❌ Không thể tải thông tin người dùng</div>';
                return;
            }
        }
        
        // Kiểm tra có student_profile không
        if (!currentUser.student_profile) {
            grid.innerHTML = '<div style="text-align:center;padding:40px;color:#ff9800;">⚠️ Không tìm thấy thông tin sinh viên. Vui lòng liên hệ admin.</div>';
            return;
        }
        
        // Lấy danh sách lớp học
        const classes = await fetchStudentClasses(currentUser.student_profile.student_id);
        
        if (classes.length === 0) {
            grid.innerHTML = '<div style="text-align:center;padding:40px;color:#666;">📚 Chưa đăng ký lớp học nào</div>';
            return;
        }
        
        // Hiển thị các lớp học
        grid.innerHTML = '';
        
        classes.forEach(cls => {
            const card = document.createElement('div');
            card.className = 'class-card';
            
            // Tính tiến độ dựa vào năm và học kỳ
            const progress = calculateProgress(cls.year, cls.semester);
            
            card.innerHTML = `
                <div class="class-name tooltip" data-tooltip="Năm: ${cls.year}, Học kỳ: ${cls.semester}">
                    ${cls.class_name}
                </div>
                <div class="class-code">Lớp: ${cls.class_id} | Năm ${cls.year} - HK${cls.semester}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:${progress}%"></div>
                </div>
                <div style="margin-top:0.5rem;font-size:0.8rem;color:#666;">
                    Tiến độ: ${progress}%
                </div>
            `;
            
            // Click vào để xem điểm
            card.addEventListener('click', () => {
                showSubjectScore(cls.class_id, cls.class_name);
            });
            
            grid.appendChild(card);
        });
        
        showNotification('✅ Đã tải danh sách lớp học');
        
    } catch (error) {
        console.error('❌ Error:', error);
        grid.innerHTML = '<div style="text-align:center;padding:40px;color:#f44336;">❌ Đã xảy ra lỗi khi tải dữ liệu</div>';
    }
}

// ===== 5. TÍNH TIẾN ĐỘ HỌC TẬP =====
function calculateProgress(year, semester) {
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1;
    
    // Nếu năm học đã qua -> 100%
    if (year < currentYear) return 100;
    
    // Nếu năm học chưa tới -> 0%
    if (year > currentYear) return 0;
    
    // Năm hiện tại
    if (semester === 1) {
        // HK1: tháng 9-1
        if (currentMonth >= 9) {
            return Math.min(Math.round(((currentMonth - 9 + 1) / 5) * 100), 100);
        } else if (currentMonth === 1) {
            return 100;
        } else {
            return 0;
        }
    } else if (semester === 2) {
        // HK2: tháng 2-6
        if (currentMonth >= 2 && currentMonth <= 6) {
            return Math.min(Math.round(((currentMonth - 2 + 1) / 5) * 100), 100);
        } else if (currentMonth > 6) {
            return 100;
        } else {
            return 0;
        }
    }
    
    return 50; // Mặc định
}

// ===== 6. HIỂN THỊ ĐIỂM CỦA MỘT LỚP =====
async function showSubjectScore(classId, className) {
    const tbody = document.getElementById('score-table-body');
    const section = document.getElementById('score-section');
    const chartSection = document.getElementById('chart-section');
    const title = document.getElementById('score-title');
    
    // Hiển thị loading
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;">⏳ Đang tải điểm...</td></tr>';
    section.style.display = 'block';
    chartSection.style.display = 'none';
    title.textContent = `📊 Điểm môn học: ${className}`;
    
    try {
        if (!currentUser || !currentUser.student_profile) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#f44336;">Không tìm thấy thông tin sinh viên</td></tr>';
            return;
        }
        
        const studentId = currentUser.student_profile.student_id;
        
        console.log(`📡 Fetching grades for student ${studentId}, class ${classId}...`);
        
        // Gọi API lấy điểm
        const response = await fetch(`${API_BASE_URL}/students/${studentId}/grades?class_id=${classId}`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Không thể lấy điểm');
        }
        
        const grades = await response.json();
        console.log('📝 Grades:', grades);
        
        if (grades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;color:#666;">📝 Chưa có điểm</td></tr>';
            return;
        }
        
        // Hiển thị điểm
        tbody.innerHTML = '';
        
        grades.forEach(grade => {
            const avg = parseFloat(grade.score).toFixed(2);
            
            const row = `
                <tr>
                    <td>${grade.subject}</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td><b style="color:#4CAF50;font-size:1.1rem;">${avg}</b></td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
        
        // Hiển thị biểu đồ
        if (grades.length > 0) {
            chartSection.style.display = 'block';
            renderScoreChart(grades);
        }
        
        showNotification('✅ Đã tải điểm thành công');
        
    } catch (error) {
        console.error('❌ Error fetching grades:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;color:#f44336;">❌ Không thể tải điểm</td></tr>';
        showNotification('Không thể tải điểm số', true);
    }
}

// ===== 7. VẼ BIỂU ĐỒ ĐIỂM =====
function renderScoreChart(grades) {
    const ctx = document.getElementById('scoreChart').getContext('2d');
    
    // Hủy biểu đồ cũ nếu có
    if (scoreChart) {
        scoreChart.destroy();
    }
    
    // Lấy tên môn và điểm
    const labels = grades.map(g => g.subject);
    const scores = grades.map(g => g.score);
    
    const colors = [
        '#DC143C',
        '#F75270',
        '#4CAF50',
        '#2196F3',
        '#FF9800',
        '#9C27B0'
    ];
    
    scoreChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Điểm',
                data: scores,
                backgroundColor: colors.slice(0, scores.length),
                borderWidth: 2,
                borderColor: '#fff',
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    ticks: {
                        stepSize: 1,
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 11
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Biểu đồ điểm các môn học',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    color: '#DC143C'
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        size: 14
                    },
                    bodyFont: {
                        size: 13
                    },
                    padding: 10,
                    cornerRadius: 5
                }
            }
        }
    });
}

// ===== 8. DARK MODE =====
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
}

// Khôi phục dark mode từ localStorage
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// ===== 9. KHỞI TẠO TRANG =====
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 studentHome.js loaded');
    
    // Kiểm tra token
    const token = localStorage.getItem('token');
    if (!token) {
        console.error('❌ No token found');
        window.location.href = '/login';
        return;
    }
    
    console.log('✅ Token found, loading data...');
    
    // Tải dữ liệu
    await generateClassCards();
});

// CSS Animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

console.log('✅ studentHome.js initialized');