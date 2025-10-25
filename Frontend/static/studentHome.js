// ===== Dữ liệu sinh viên =====
const studentData = {
    name: "Nguyễn Văn An",
    id: "SV001234",
    class: "CNTT-K15",
    birth: "15/03/2002"
};

// ===== Dữ liệu lớp học =====
const classesData = [
    { id: 1, name: "Lập trình Web", code: "IT301", progress: 75, instructor: "TS. Nguyễn Văn B" },
    { id: 2, name: "Cơ sở dữ liệu", code: "IT302", progress: 60, instructor: "PGS. Trần Thị C" },
    { id: 3, name: "Mạng máy tính", code: "IT303", progress: 45, instructor: "ThS. Lê Văn D" },
    { id: 4, name: "Trí tuệ nhân tạo", code: "IT304", progress: 30, instructor: "GS. Phạm Thị E" }
];

// ===== Dữ liệu điểm thành phần =====
const scoreData = [
    { subject: "Lập trình Web", cc: 9, gk: 8, ck: 8.5 },
    { subject: "Cơ sở dữ liệu", cc: 8, gk: 7.5, ck: 8 },
    { subject: "Mạng máy tính", cc: 8.5, gk: 8, ck: 8.5 },
    { subject: "Trí tuệ nhân tạo", cc: 9, gk: 9, ck: 9.2 }
];

let scoreChart = null;

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
            <div class="progress-bar"><div class="progress-fill" style="width:${cls.progress}%"></div></div>
            <div style="margin-top:0.5rem;font-size:0.8rem;color:#666;">Tiến độ: ${cls.progress}%</div>
        `;
        card.addEventListener('click', () => showSubjectScore(cls.name));
        grid.appendChild(card);
    });
}

// ===== Hiển thị điểm của 1 môn =====
function showSubjectScore(subjectName) {
    const subject = scoreData.find(s => s.subject === subjectName);
    if (!subject) return;

    const tbody = document.getElementById('score-table-body');
    const section = document.getElementById('score-section');
    const chartSection = document.getElementById('chart-section');
    const title = document.getElementById('score-title');

    tbody.innerHTML = '';
    title.textContent = `📊 Điểm môn học: ${subjectName}`;
    section.style.display = 'block';
    chartSection.style.display = 'block';

    const avg = ((subject.cc * 0.1) + (subject.gk * 0.3) + (subject.ck * 0.6)).toFixed(2);
    const row = `
        <tr>
            <td>${subject.subject}</td>
            <td>${subject.cc}</td>
            <td>${subject.gk}</td>
            <td>${subject.ck}</td>
            <td><b>${avg}</b></td>
        </tr>
    `;
    tbody.innerHTML = row;

    renderScoreChart(subject);
}

// ===== Biểu đồ điểm của 1 môn =====
function renderScoreChart(subject) {
    const ctx = document.getElementById('scoreChart').getContext('2d');
    if (scoreChart) scoreChart.destroy();

    scoreChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Chuyên cần', 'Giữa kỳ', 'Cuối kỳ', 'Trung bình'],
            datasets: [{
                label: subject.subject,
                data: [subject.cc, subject.gk, subject.ck, ((subject.cc * 0.1) + (subject.gk * 0.3) + (subject.ck * 0.6)).toFixed(2)],
                backgroundColor: ['#DC143C', '#F75270', '#F7CAC9', '#999']
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, max: 10 }
            },
            plugins: { legend: { display: false } }
        }
    });
}

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
