// ===== CẤU HÌNH API =====
const API_BASE_URL = 'http://127.0.0.1:8000/api';

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
    document.getElementById('student-name').textContent = userData.full_name || 'N/A';

    if (userData.role === 'student' && userData.student_profile) {
        const profile = userData.student_profile;

        document.getElementById('student-id').textContent = profile.student_code || 'N/A';

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
        if (!currentUser) {
            const user = await fetchCurrentUser();
            if (!user) {
                grid.innerHTML = '<div style="text-align:center;padding:40px;color:#f44336;">❌ Không thể tải thông tin người dùng</div>';
                return;
            }
        }

        if (!currentUser.student_profile) {
            grid.innerHTML = '<div style="text-align:center;padding:40px;color:#ff9800;">⚠️ Không tìm thấy thông tin sinh viên. Vui lòng liên hệ admin.</div>';
            return;
        }

        const classes = await fetchStudentClasses(currentUser.student_profile.student_id);

        if (classes.length === 0) {
            grid.innerHTML = '<div style="text-align:center;padding:40px;color:#666;">📚 Chưa đăng ký lớp học nào</div>';
            return;
        }

        grid.innerHTML = '';

        classes.forEach(cls => {
            const card = document.createElement('div');
            card.className = 'class-card';

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

    if (year < currentYear) return 100;
    if (year > currentYear) return 0;

    if (semester === 1) {
        if (currentMonth >= 9) {
            return Math.min(Math.round(((currentMonth - 9 + 1) / 5) * 100), 100);
        } else if (currentMonth === 1) {
            return 100;
        } else {
            return 0;
        }
    } else if (semester === 2) {
        if (currentMonth >= 2 && currentMonth <= 6) {
            return Math.min(Math.round(((currentMonth - 2 + 1) / 5) * 100), 100);
        } else if (currentMonth > 6) {
            return 100;
        } else {
            return 0;
        }
    }

    return 50;
}

// ✅ HÀM GỘP ĐIỂM THEO LỚP HỌC
function groupGradesByClass(grades) {
    // Group grades by class_id
    const grouped = {};

    grades.forEach(grade => {
        const classId = grade.class_id;

        if (!grouped[classId]) {
            grouped[classId] = {
                class_id: classId,
                attendance: null,
                mid: null,
                final: null
            };
        }

        // Map subject name to field
        const subject = grade.subject.toLowerCase();
        if (subject === 'attendance') {
            grouped[classId].attendance = grade.score;
        } else if (subject === 'mid') {
            grouped[classId].mid = grade.score;
        } else if (subject === 'final') {
            grouped[classId].final = grade.score;
        }
    });

    return Object.values(grouped);
}

// ✅ HÀM TÍNH ĐIỂM TRUNG BÌNH
function calculateAverage(attendance, mid, final) {
    // Chỉ tính trung bình nếu có ít nhất 1 điểm
    const scores = [];
    const weights = [];

    if (attendance !== null && attendance !== undefined) {
        scores.push(parseFloat(attendance));
        weights.push(0.2);
    }
    if (mid !== null && mid !== undefined) {
        scores.push(parseFloat(mid));
        weights.push(0.3);
    }
    if (final !== null && final !== undefined) {
        scores.push(parseFloat(final));
        weights.push(0.5);
    }

    if (scores.length === 0) return null;

    // Tính trọng số tương đối
    const totalWeight = weights.reduce((sum, w) => sum + w, 0);
    const weightedSum = scores.reduce((sum, score, i) => sum + (score * weights[i]), 0);

    return (weightedSum / totalWeight).toFixed(2);
}

// ===== 6. HIỂN THỊ ĐIỂM CỦA MỘT LỚP =====
async function showSubjectScore(classId, className) {
    const tbody = document.getElementById('score-table-body');
    const section = document.getElementById('score-section');
    const chartSection = document.getElementById('chart-section');
    const title = document.getElementById('score-title');

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

        const response = await fetch(`${API_BASE_URL}/students/${studentId}/grades?class_id=${classId}`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Không thể lấy điểm');
        }

        const grades = await response.json();
        console.log('📝 Raw grades:', grades);

        if (grades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;color:#666;">📝 Chưa có điểm</td></tr>';
            return;
        }

        // ✅ GỘP ĐIỂM THEO LỚP
        const groupedGrades = groupGradesByClass(grades);
        console.log('📊 Grouped grades:', groupedGrades);

        tbody.innerHTML = '';

        groupedGrades.forEach(gradeGroup => {
            const att = gradeGroup.attendance !== null ? gradeGroup.attendance : '-';
            const mid = gradeGroup.mid !== null ? gradeGroup.mid : '-';
            const fin = gradeGroup.final !== null ? gradeGroup.final : '-';
            const avg = calculateAverage(gradeGroup.attendance, gradeGroup.mid, gradeGroup.final);

            const row = `
                <tr>
                    <td>${className}</td>
                    <td>${att !== '-' ? parseFloat(att).toFixed(2) : '-'}</td>
                    <td>${mid !== '-' ? parseFloat(mid).toFixed(2) : '-'}</td>
                    <td>${fin !== '-' ? parseFloat(fin).toFixed(2) : '-'}</td>
                    <td><b style="color:#4CAF50;font-size:1.1rem;">${avg !== null ? avg : '-'}</b></td>
                </tr>
            `;
            tbody.innerHTML += row;
        });

        // ✅ VẼ BIỂU ĐỒ
        if (groupedGrades.length > 0) {
            chartSection.style.display = 'block';
            renderScoreChart(groupedGrades, className);
        }

        showNotification('✅ Đã tải điểm thành công');

    } catch (error) {
        console.error('❌ Error fetching grades:', error);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;color:#f44336;">❌ Không thể tải điểm</td></tr>';
        showNotification('Không thể tải điểm số', true);
    }
}

// ===== 7. VẼ BIỂU ĐỒ ĐIỂM =====
function renderScoreChart(groupedGrades, className) {
    const ctx = document.getElementById('scoreChart').getContext('2d');

    if (scoreChart) {
        scoreChart.destroy();
    }

    // ✅ Dữ liệu cho biểu đồ
    const labels = ['Chuyên cần', 'Giữa kỳ', 'Cuối kỳ'];
    const gradeGroup = groupedGrades[0]; // Lấy nhóm điểm đầu tiên

    const scores = [
        gradeGroup.attendance || 0,
        gradeGroup.mid || 0,
        gradeGroup.final || 0
    ];

    const colors = ['#DC143C', '#F75270', '#4CAF50'];

    scoreChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Điểm',
                data: scores,
                backgroundColor: colors,
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
                    text: `Biểu đồ điểm: ${className}`,
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

if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// ===== 9. KHỞI TẠO TRANG =====
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 studentHome.js loaded');

    const token = localStorage.getItem('token');
    if (!token) {
        console.error('❌ No token found');
        window.location.href = '/login';
        return;
    }

    console.log('✅ Token found, loading data...');

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