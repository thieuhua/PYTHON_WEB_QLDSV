// ========================================
// studentHome.js — Final (UI-upgraded, logic preserved)
// - Giữ nguyên API endpoints & logic gốc
// - Removes inline color for progress, adds .progress-text
// - Injects Dark Mode button into header (no HTML change required)
// ========================================

const API_BASE_URL = 'http://127.0.0.1:8000/api';
let scoreChart = null;
let currentUser = null;

// ===== Helpers =====
function getAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
}

function showNotification(message, isError = false) {
  const notif = document.createElement('div');
  notif.style.cssText = `
    position: fixed;
    top: -60px;
    left: 50%;
    transform: translateX(-50%);
    background: ${isError ? '#f44336' : '#4CAF50'};
    color: white;
    padding: 14px 24px;
    border-radius: 8px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    font-size: 15px;
    font-weight: 500;
    z-index: 9999;
    opacity: 0;
    transition: all 0.4s ease;
  `;
  notif.textContent = message;
  document.body.appendChild(notif);

  // Hiện ra (trượt xuống)
  setTimeout(() => {
    notif.style.top = '30px';
    notif.style.opacity = '1';
  }, 20);

  // Ẩn đi (trượt lên lại)
  setTimeout(() => {
    notif.style.top = '-60px';
    notif.style.opacity = '0';
    setTimeout(() => notif.remove(), 400);
  }, 3500);
}

// ===== 1. Fetch current user =====
async function fetchCurrentUser() {
  try {
    const resp = await fetch(`/api/me`, { headers: getAuthHeaders() });
    if (!resp.ok) throw new Error('Không thể lấy thông tin người dùng');
    const data = await resp.json();
    currentUser = data;
    renderStudentInfo(data);
    return data;
  } catch (err) {
    console.error('fetchCurrentUser error', err);
    showNotification('Không thể tải thông tin sinh viên', true);
    return null;
  }
}

// ===== 2. Render student info =====
function renderStudentInfo(userData) {
  if (!userData) return;
  const nameEl = document.getElementById('student-name');
  if (nameEl) nameEl.textContent = userData.full_name || 'N/A';

  if (userData.role === 'student' && userData.student_profile) {
    const profile = userData.student_profile;
    const idEl = document.getElementById('student-id');
    const classEl = document.getElementById('student-class');
    const birthEl = document.getElementById('birth-date');
    if (idEl) idEl.textContent = profile.student_code || 'N/A';
    if (classEl) classEl.textContent = 'Sinh viên';
    if (birthEl) {
      if (profile.birthdate) {
        const d = new Date(profile.birthdate);
        birthEl.textContent = `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${d.getFullYear()}`;
      } else birthEl.textContent = 'N/A';
    }
  }
}

// ===== 3. Fetch enrollments & class details =====
async function fetchStudentClasses(studentId) {
  try {
    const enrollRes = await fetch(`${API_BASE_URL}/students/${studentId}/enrollments`, { headers: getAuthHeaders() });
    if (!enrollRes.ok) throw new Error('Không thể lấy danh sách lớp học');
    const enrollments = await enrollRes.json();
    if (!Array.isArray(enrollments) || enrollments.length === 0) return [];

    // load class details in parallel
    const promises = enrollments.map(async (enroll) => {
      try {
        const clsRes = await fetch(`${API_BASE_URL}/classes/${enroll.class_id}`, { headers: getAuthHeaders() });
        if (!clsRes.ok) return null;
        return await clsRes.json();
      } catch (e) {
        console.error('fetch class error', enroll.class_id, e);
        return null;
      }
    });

    const classes = await Promise.all(promises);
    return classes.filter(c => c !== null);
  } catch (err) {
    console.error('fetchStudentClasses error', err);
    showNotification('Không thể tải danh sách lớp học', true);
    return [];
  }
}

// ===== 4. Generate class cards (uses .progress-text class, no inline color) =====
async function generateClassCards() {
  const grid = document.getElementById('classes-grid');
  if (!grid) return;

  grid.innerHTML = `<div style="text-align:center;padding:40px;color:#666;">⏳ Đang tải danh sách lớp học...</div>`;

  if (!currentUser) {
    const u = await fetchCurrentUser();
    if (!u) {
      grid.innerHTML = `<div style="text-align:center;padding:40px;color:#f44336;">❌ Không thể tải thông tin người dùng</div>`;
      return;
    }
  }

  if (!currentUser.student_profile) {
    grid.innerHTML = `<div style="text-align:center;padding:40px;color:#ff9800;">⚠️ Không tìm thấy thông tin sinh viên. Vui lòng liên hệ admin.</div>`;
    return;
  }

  const studentId = currentUser.student_profile.student_id;
  const classes = await fetchStudentClasses(studentId);

  if (!classes || classes.length === 0) {
    grid.innerHTML = `<div style="text-align:center;padding:40px;color:#666;">📚 Chưa đăng ký lớp học nào</div>`;
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
                <div class="progress-text">
                    Tiến độ: ${progress}%
                </div>
            `;

    card.addEventListener('click', () => showSubjectScore(cls.class_id, cls.class_name));
    grid.appendChild(card);
  });

  showNotification('✅ Đã tải danh sách lớp học');
}

// ===== 5. Progress calculation (keep same logic semantics) =====
function calculateProgress(year, semester) {
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

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

// ===== 6. Group grades + calculate average (preserve original mapping) =====
function groupGradesByClass(grades) {
  const grouped = {};
  grades.forEach(grade => {
    const classId = grade.class_id;
    if (!grouped[classId]) grouped[classId] = { class_id: classId, attendance: null, mid: null, final: null };

    const subject = (grade.subject || '').toLowerCase();
    if (subject === 'attendance') grouped[classId].attendance = grade.score;
    else if (subject === 'mid') grouped[classId].mid = grade.score;
    else if (subject === 'final') grouped[classId].final = grade.score;
  });
  return Object.values(grouped);
}

function calculateAverage(attendance, mid, finalScore) {
  const scores = [];
  const weights = [];
  if (attendance !== null && attendance !== undefined) { scores.push(parseFloat(attendance)); weights.push(0.2); }
  if (mid !== null && mid !== undefined) { scores.push(parseFloat(mid)); weights.push(0.3); }
  if (finalScore !== null && finalScore !== undefined) { scores.push(parseFloat(finalScore)); weights.push(0.5); }
  if (scores.length === 0) return null;
  const totalWeight = weights.reduce((s, w) => s + w, 0);
  const weightedSum = scores.reduce((s, v, i) => s + v * weights[i], 0);
  return (weightedSum / totalWeight).toFixed(2);
}

// ===== 7. Show scores for a class and render chart =====
async function showSubjectScore(classId, className) {
  const tbody = document.getElementById('score-table-body');
  const section = document.getElementById('score-section');
  const chartSection = document.getElementById('chart-section');
  const title = document.getElementById('score-title');

  if (!tbody || !section || !chartSection || !title) return;

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
    const res = await fetch(`${API_BASE_URL}/students/${studentId}/grades?class_id=${classId}`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Không thể lấy điểm');
    const grades = await res.json();

    if (!grades || grades.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;color:#666;">📝 Chưa có điểm</td></tr>';
      return;
    }

    const grouped = groupGradesByClass(grades);
    tbody.innerHTML = '';

    grouped.forEach(gradeGroup => {
      const att = gradeGroup.attendance !== null ? parseFloat(gradeGroup.attendance).toFixed(2) : '-';
      const mid = gradeGroup.mid !== null ? parseFloat(gradeGroup.mid).toFixed(2) : '-';
      const fin = gradeGroup.final !== null ? parseFloat(gradeGroup.final).toFixed(2) : '-';
      const avg = calculateAverage(gradeGroup.attendance, gradeGroup.mid, gradeGroup.final);
      const avgDisplay = avg !== null ? avg : '-';
      tbody.innerHTML += `
        <tr>
          <td>${className}</td>
          <td>${att}</td>
          <td>${mid}</td>
          <td>${fin}</td>
          <td><b style="color:#4CAF50">${avgDisplay}</b></td>
        </tr>
      `;
    });

    // render chart if at least one group
    if (grouped.length > 0) {
      chartSection.style.display = 'block';
      renderScoreChart(grouped, className);
    } else {
      chartSection.style.display = 'none';
    }

    showNotification('✅ Đã tải điểm thành công');
  } catch (err) {
    console.error('showSubjectScore error', err);
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;color:#f44336;">❌ Không thể tải điểm</td></tr>';
    showNotification('Không thể tải điểm', true);
  }
}

// ===== 8. Render chart (uses Chart.js already included in HTML) =====
function renderScoreChart(groupedGrades, className) {
  const ctxEl = document.getElementById('scoreChart');
  if (!ctxEl) return;
  const ctx = ctxEl.getContext('2d');

  if (scoreChart) try { scoreChart.destroy(); } catch(e){}

  const g = groupedGrades[0] || { attendance: 0, mid: 0, final: 0 };
  const data = [
    g.attendance !== null ? parseFloat(g.attendance) : 0,
    g.mid !== null ? parseFloat(g.mid) : 0,
    g.final !== null ? parseFloat(g.final) : 0
  ];

  scoreChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Chuyên cần', 'Giữa kỳ', 'Cuối kỳ'],
      datasets: [{
        label: 'Điểm',
        data,
        backgroundColor: ['#DC143C', '#F75270', '#4CAF50'],
        borderWidth: 0,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: { beginAtZero: true, max: 10, ticks: { stepSize: 1 } }
      },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: `Biểu đồ điểm: ${className}`,
          color: '#DC143C',
          font: { size: 14, weight: '600' }
        }
      }
    }
  });
}

// ===== 9. Dark mode toggle logic (keeps state in localStorage) =====
function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  const isDark = document.body.classList.contains('dark-mode');
  localStorage.setItem('darkMode', isDark ? 'true' : 'false');
}
function initDarkModeFromStorage() {
  if (localStorage.getItem('darkMode') === 'true') document.body.classList.add('dark-mode');
}

// ===== 10. Join class =====
async function JoinClass() {
  try {
    const resp = await fetch(`/api/me`, { headers: getAuthHeaders() });
    if (!resp.ok) throw new Error('Không thể lấy thông tin người dùng');
    const userData = await resp.json();
    const studentId = parseInt(userData.student_profile.student_id);
    const joinCode = (document.querySelector('.code-input')?.value || '').trim();

    const res = await fetch(`${API_BASE_URL}/student/${studentId}/join`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: joinCode })
    });

    const data = await res.json();
    showNotification(data.message, !res.ok);
    if (res.ok) {
      // refresh class list shortly to show new class
      setTimeout(() => generateClassCards(), 900);
    }
  } catch (err) {
    console.error('JoinClass error', err);
    showNotification('❌ Không thể tham gia lớp', true);
  }
}

// ===== 11. Edit profile redirect (kept original behavior) =====
function editProfile() {
  window.location.href = '/editProfile';
}

// ===== 12. Auto update on focus & storage changes =====
window.addEventListener('focus', async () => {
  try { await fetchCurrentUser(); await generateClassCards(); } catch(e){}
});
window.addEventListener('storage', async (e) => {
  if (e.key === 'userInfo') {
    try {
      const updated = JSON.parse(e.newValue);
      renderStudentInfo(updated);
    } catch (err) { console.error('storage parse error', err); }
  }
});

// ===== 13. Inject header dark mode button (so no HTML changes needed) =====
function ensureHeaderDarkToggle() {
  try {
    const headerButtons = document.querySelector('.header-buttons');
    if (!headerButtons) return;

    // If button already exists, attach listener and return
    if (document.getElementById('injected-dark-toggle')) {
      const btn = document.getElementById('injected-dark-toggle');
      btn.onclick = toggleDarkMode;
      return;
    }

    const btn = document.createElement('button');
    btn.id = 'injected-dark-toggle';
    btn.className = 'dark-mode-toggle';
    btn.title = 'Chuyển chế độ tối/sáng';
    btn.innerText = '🌙';
    btn.onclick = toggleDarkMode;

    // insert before the last header button (so sits near logout/edit)
    headerButtons.insertBefore(btn, headerButtons.lastElementChild?.nextSibling);
  } catch (err) {
    console.error('ensureHeaderDarkToggle error', err);
  }
}

// ===== 14. Init on DOMContentLoaded =====
document.addEventListener('DOMContentLoaded', async () => {
  // ensure token exists (original behavior)
  const token = localStorage.getItem('token');
  if (!token) {
    console.error('No token found, redirect to /login');
    window.location.href = '/login';
    return;
  }

  // init dark mode state & inject button
  initDarkModeFromStorage();
  ensureHeaderDarkToggle();

  // load user and classes
  await fetchCurrentUser();
  await generateClassCards();

  console.log('✅ studentHome.js initialized');
});

// expose some functions for inline HTML buttons (if used)
window.JoinClass = JoinClass;
window.editProfile = editProfile;
window.toggleDarkMode = toggleDarkMode;
