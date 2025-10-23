// ===== Kiểm tra token đăng nhập =====
let token = localStorage.getItem('token');
if (!token) {
    console.warn("Không có token, dùng dữ liệu giả lập.");
}

// ===== Dữ liệu sinh viên =====
const studentData = {
    name: "Nguyễn Văn An",
    id: "SV001234",
    class: "CNTT-K15",
    birth: "15/03/2002"
};

// ===== Dữ liệu lớp học =====
const classesData = [
    {
        id: 1,
        name: "Lập trình Web",
        code: "IT301",
        schedule: [
            { day: "Thứ 2", time: "07:00 - 09:30", room: "A101" },
            { day: "Thứ 4", time: "13:00 - 15:30", room: "A101" }
        ],
        progress: 75,
        instructor: "TS. Nguyễn Văn B"
    },
    {
        id: 2,
        name: "Cơ sở dữ liệu",
        code: "IT302",
        schedule: [
            { day: "Thứ 3", time: "07:00 - 09:30", room: "B201" },
            { day: "Thứ 6", time: "09:30 - 12:00", room: "B201" }
        ],
        progress: 60,
        instructor: "PGS. Trần Thị C"
    },
    {
        id: 3,
        name: "Mạng máy tính",
        code: "IT303",
        schedule: [
            { day: "Thứ 5", time: "13:00 - 15:30", room: "C301" },
            { day: "Thứ 7", time: "07:00 - 09:30", room: "C301" }
        ],
        progress: 45,
        instructor: "ThS. Lê Văn D"
    },
    {
        id: 4,
        name: "Trí tuệ nhân tạo",
        code: "IT304",
        schedule: [
            { day: "Thứ 2", time: "13:00 - 15:30", room: "D401" },
            { day: "Thứ 4", time: "07:00 - 09:30", room: "D401" }
        ],
        progress: 30,
        instructor: "GS. Phạm Thị E"
    }
];

// ===== Dữ liệu điểm thành phần =====
const scoreData = [
    { subject: "Lập trình Web", cc: 9, gk: 8, ck: 8.5 },
    { subject: "Cơ sở dữ liệu", cc: 8, gk: 7.5, ck: 8 },
    { subject: "Mạng máy tính", cc: 8.5, gk: 8, ck: 8.5 },
    { subject: "Trí tuệ nhân tạo", cc: 9, gk: 9, ck: 9.2 }
];

// ===== Hiển thị thông tin sinh viên =====
function renderStudentInfo(data) {
    document.getElementById('student-name').textContent = data.name;
    document.getElementById('student-id').textContent = data.id;
    document.getElementById('student-class').textContent = data.class;
    document.getElementById('birth-date').textContent = data.birth;
}

// ===== Sinh danh sách lớp học =====
function generateClassCards(classes = classesData) {
    const grid = document.getElementById('classes-grid');
    grid.innerHTML = '';
    classes.forEach(cls => {
        const card = document.createElement('div');
        card.className = 'class-card';
        card.innerHTML = `
            <div class="class-name tooltip" data-tooltip="Giảng viên: ${cls.instructor}">${cls.name}</div>
            <div class="class-code">Mã lớp: ${cls.code}</div>
            <div class="class-schedule">
                ${cls.schedule.map(s => `
                    <div class="schedule-item">
                        <span>📅</span>
                        <span>${s.day}: ${s.time}</span>
                        <span>🏫 ${s.room}</span>
                    </div>
                `).join('')}
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width:${cls.progress}%"></div>
            </div>
            <div style="margin-top:0.5rem;font-size:0.8rem;color:#666;">
                Tiến độ: ${cls.progress}%
            </div>
        `;
        grid.appendChild(card);
    });
}

// ===== Hiển thị bảng điểm =====
function renderScoreTable(data) {
    const tbody = document.getElementById('score-table-body');
    tbody.innerHTML = '';
    data.forEach(item => {
        const avg = ((item.cc * 0.1) + (item.gk * 0.3) + (item.ck * 0.6)).toFixed(2);
        const row = `
            <tr>
                <td>${item.subject}</td>
                <td>${item.cc}</td>
                <td>${item.gk}</td>
                <td>${item.ck}</td>
                <td><b>${avg}</b></td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

// ===== Biểu đồ điểm trung bình =====
function renderScoreChart(data) {
    const ctx = document.getElementById('scoreChart').getContext('2d');
    const labels = data.map(d => d.subject);
    const avgScores = data.map(d => ((d.cc * 0.1) + (d.gk * 0.3) + (d.ck * 0.6)).toFixed(2));

    new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Điểm trung bình',
                data: avgScores,
                borderColor: '#DC143C',
                backgroundColor: '#F75270',
                fill: false,
                tension: 0.3
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, max: 10 }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// ===== Tìm kiếm lớp học =====
document.getElementById('search-input').addEventListener('input', e => {
    const value = e.target.value.toLowerCase();
    const filtered = classesData.filter(c =>
        c.name.toLowerCase().includes(value) ||
        c.code.toLowerCase().includes(value)
    );
    generateClassCards(filtered);
});

// ===== Dark mode =====
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
}

// ===== Đăng xuất =====
function handleLogout() {
    alert('Đăng xuất thành công!');
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// ===== Khởi tạo trang =====
renderStudentInfo(studentData);
generateClassCards();
renderScoreTable(scoreData);
renderScoreChart(scoreData);
