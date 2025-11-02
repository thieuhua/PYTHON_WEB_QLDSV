// teacherHome.js — full file (y hệt yêu cầu), đồng bộ studentHome UI, fix chức năng

const API_BASE_URL = '/api';
let teacherClasses = [];
let currentClass = null;

// ---------- Helpers ----------
function getAuthHeaders() {
  const token = localStorage.getItem('token') || getCookie('token');
  return {
    'Authorization': token ? `Bearer ${token}` : '',
    'Content-Type': 'application/json'
  };
}
function getCookie(name) {
  const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}
function notify(msg, isError = false) {
  const c = document.getElementById('notif-container');
  if (!c) return;
  const el = document.createElement('div');
  el.style.cssText = `
    position: relative;
    background: ${isError ? '#f44336' : '#4CAF50'};
    color: white;
    padding: 10px 14px;
    border-radius: 10px;
    margin-top:8px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.12);
    font-weight:600;
  `;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

// ---------- Dark mode helper (inject button like studentHome) ----------
function ensureHeaderDarkToggle() {
  try {
    const headerButtons = document.querySelector('.header-buttons');
    if (!headerButtons) return;
    if (document.getElementById('injected-dark-toggle')) {
      document.getElementById('injected-dark-toggle').onclick = toggleDarkMode;
      return;
    }
    const btn = document.createElement('button');
    btn.id = 'injected-dark-toggle';
    btn.className = 'dark-mode-toggle';
    btn.title = 'Chuyển chế độ tối/sáng';
    btn.innerText = '🌙';
    btn.onclick = toggleDarkMode;
    headerButtons.insertBefore(btn, headerButtons.lastElementChild);
  } catch (err) {
    console.error('ensureHeaderDarkToggle error', err);
  }
}
function initDarkModeFromStorage() {
  if (localStorage.getItem('darkMode') === 'true') document.body.classList.add('dark-mode');
}
function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  localStorage.setItem('darkMode', document.body.classList.contains('dark-mode') ? 'true' : 'false');
}

// ---------- Fetch user info ----------
async function fetchUser() {
  try {
    const res = await fetch(`${API_BASE_URL}/me`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const user = await res.json();
    document.getElementById('teacher-name').textContent = user.full_name || '—';
    document.getElementById('teacher-email').textContent = user.email || '—';
  } catch (err) {
    console.error('fetchUser error', err);
  }
}

// ---------- Fetch classes ----------
async function fetchClasses() {
  try {
    const res = await fetch(`${API_BASE_URL}/teacher/classes`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Không tải được danh sách lớp');
    teacherClasses = await res.json();
    renderClassCards();
  } catch (err) {
    console.error(err);
    notify('Không tải được danh sách lớp', true);
    const grid = document.getElementById('classes-grid');
    if (grid) grid.innerHTML = `<div style="padding:1rem;color:#f44336">Lỗi khi tải danh sách lớp</div>`;
  }
}

// ---------- Render class cards (fix click overlay by using event listeners) ----------
function renderClassCards() {
  const grid = document.getElementById('classes-grid');
  if (!grid) return;
  if (!teacherClasses || teacherClasses.length === 0) {
    grid.innerHTML = `<div style="padding:1rem;color:#666;">Chưa có lớp học nào</div>`;
    return;
  }

  grid.innerHTML = teacherClasses.map(c => {
    const count = c.current_students ?? (Array.isArray(c.students) ? c.students.length : 0);
    return `
      <div class="class-card" data-id="${c.class_id}">
        <div class="class-name">${escapeHtml(c.class_name)}</div>
        <div class="class-meta"><b>Mã:</b> ${c.class_id} • <b>Năm:</b> ${c.year}</div>
        <div class="class-meta">SV: ${count}</div>
        <div style="text-align:center;margin-top:10px;">
          <button class="class-detail-btn" data-id="${c.class_id}">Chi tiết</button>
        </div>
      </div>
    `;
  }).join('');

  // Gắn click riêng cho nút Chi tiết
  document.querySelectorAll('.class-detail-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const id = btn.dataset.id;
      openClassModal(id);
    });
  });
}

// ---------- Create class ----------
async function createClass(name, code) {
  try {
    const now = new Date();
    const body = {
      class_name: name,
      class_code: code || undefined,
      year: now.getFullYear(),
      semester: now.getMonth() + 1 >= 6 ? 1 : 2
    };
    const res = await fetch(`${API_BASE_URL}/teacher/classes`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      const text = await res.text().catch(()=>null);
      throw new Error(text || 'Lỗi tạo lớp');
    }
    notify('✅ Tạo lớp thành công');
    await fetchClasses();
  } catch (err) {
    console.error('createClass', err);
    notify('Lỗi khi tạo lớp', true);
  }
}

// ---------- Open class modal & fetch students ----------
async function fetchClassDetail(id) {
  try {
    const res = await fetch(`${API_BASE_URL}/teacher/classes/${id}`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Không tải được dữ liệu lớp');
    return await res.json();
  } catch (err) {
    console.error('fetchClassDetail', err);
    notify('Không tải được dữ liệu lớp', true);
    return null;
  }
}

async function openClassModal(id) {
  try {
    const cls = await fetchClassDetail(id);
    if (!cls) return;
    currentClass = cls;
    document.getElementById('modal-class-name').textContent = cls.class_name || 'Tên lớp';
    document.getElementById('modal-class-code').textContent = cls.class_id ?? '-';
    document.getElementById('modal-class-join-code').textContent = cls.join_code ?? '-';
    document.getElementById('modal-count').textContent = cls.students?.length ?? 0;
    document.getElementById('class-modal').classList.remove('hidden');
    renderStudentTable();
  } catch (err) {
    console.error('openClassModal', err);
    notify('Không mở được chi tiết lớp', true);
  }
}

// ---------- Close modal ----------
function closeModal() {
  document.getElementById('class-modal').classList.add('hidden');
  currentClass = null;
  // clear table & select all
  document.getElementById('student-tbody').innerHTML = '';
  const sa = document.getElementById('select-all'); if (sa) sa.checked = false;
}

// ---------- Render student table (fixed columns) ----------
function renderStudentTable() {
  const tbody = document.getElementById('student-tbody');
  if (!tbody) return;
  if (!currentClass || !Array.isArray(currentClass.students) || currentClass.students.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9"><em>Chưa có sinh viên trong lớp</em></td></tr>`;
    return;
  }

  tbody.innerHTML = currentClass.students.map((s, i) => {
    const g = s.grades || {};
    const att = g.attendance !== undefined && g.attendance !== null ? g.attendance : '';
    const mid = g.midterm !== undefined && g.midterm !== null ? g.midterm : '';
    const fin = g.final !== undefined && g.final !== null ? g.final : '';
    const avg = (att !== '' && mid !== '' && fin !== '') ? ((parseFloat(att)*0.2 + parseFloat(mid)*0.3 + parseFloat(fin)*0.5).toFixed(1)) : '-';
    return `
      <tr data-stu-id="${s.student_id}">
        <td><input type="checkbox" class="select-stu" data-id="${s.student_id}"></td>
        <td>${i+1}</td>
        <td style="text-align:left;padding-left:12px;">${escapeHtml(s.full_name)}</td>
        <td>${escapeHtml(s.student_code)}</td>
        <td><input class="input-grade" data-field="attendance" value="${att}" onchange="onGradeEdit('${s.student_id}', this)"></td>
        <td><input class="input-grade" data-field="midterm" value="${mid}" onchange="onGradeEdit('${s.student_id}', this)"></td>
        <td><input class="input-grade" data-field="final" value="${fin}" onchange="onGradeEdit('${s.student_id}', this)"></td>
        <td><strong>${avg}</strong></td>
        <td><button class="create-btn small danger" onclick="deleteStudentFromClass('${s.student_id}')">Xóa</button></td>
      </tr>
    `;
  }).join('');
}

// ---------- Grade edit ----------
function onGradeEdit(stuId, input) {
  const field = input.dataset.field;
  const v = input.value.trim();
  if (v === '') return;
  const num = Number(v);
  if (isNaN(num) || num < 0 || num > 10) {
    notify('Điểm không hợp lệ (0-10)', true);
    return;
  }
  updateStudentGrade(stuId, field, num);
}

async function updateStudentGrade(studentId, field, val) {
  if (!currentClass) return notify('Không có lớp hiện tại', true);
  try {
    const payload = [{
      student_id: parseInt(studentId),
      class_id: parseInt(currentClass.class_id),
      subject: field === 'midterm' ? 'mid' : (field === 'final' ? 'final' : 'attendance'),
      score: Number(val)
    }];
    const res = await fetch(`${API_BASE_URL}/teacher/classes/${currentClass.class_id}/grades`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const text = await res.text().catch(()=>null);
      throw new Error(text || 'Cập nhật điểm thất bại');
    }
    notify('Cập nhật điểm thành công');
    // refresh class details
    const updated = await fetchClassDetail(currentClass.class_id);
    if (updated) {
      currentClass = updated;
      renderStudentTable();
    }
  } catch (err) {
    console.error('updateStudentGrade', err);
    notify('Cập nhật điểm thất bại', true);
  }
}

// ---------- Add student (manual) ----------
async function addStudentManual() {
  if (!currentClass) return notify('Mở chi tiết lớp trước khi thêm SV', true);
  const name = (document.getElementById('add-student-name')?.value || '').trim();
  const code = (document.getElementById('add-student-id')?.value || '').trim();
  if (!name || !code) {
    document.getElementById('add-student-warning').textContent = 'Vui lòng nhập Họ tên và Mã SV';
    return;
  }
  document.getElementById('add-student-warning').textContent = '';
  try {
    const res = await fetch(`${API_BASE_URL}/teacher/classes/${currentClass.class_id}/students`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ full_name: name, student_code: code })
    });
    if (!res.ok) {
      const txt = await res.text().catch(()=>null);
      throw new Error(txt || 'Thêm sinh viên thất bại');
    }
    notify('Đã thêm sinh viên');
    const updated = await fetchClassDetail(currentClass.class_id);
    if (updated) {
      currentClass = updated;
      renderStudentTable();
      document.getElementById('modal-count').textContent = currentClass.students?.length ?? 0;
    }
    document.getElementById('add-student-name').value = '';
    document.getElementById('add-student-id').value = '';
  } catch (err) {
    console.error('addStudentManual', err);
    notify('Thêm sinh viên thất bại', true);
  }
}

// ---------- Delete single student ----------
async function deleteStudentFromClass(studentId) {
  if (!currentClass) return;
  if (!confirm('Xóa sinh viên này khỏi lớp?')) return;
  try {
    const res = await fetch(`${API_BASE_URL}/teacher/classes/${currentClass.class_id}/students/${studentId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Xóa thất bại');
    notify('Đã xóa sinh viên');
    const updated = await fetchClassDetail(currentClass.class_id);
    if (updated) {
      currentClass = updated;
      renderStudentTable();
      document.getElementById('modal-count').textContent = currentClass.students?.length ?? 0;
    }
  } catch (err) {
    console.error('deleteStudentFromClass', err);
    notify('Xóa thất bại', true);
  }
}

// ---------- Delete selected students (bulk) ----------
async function deleteSelectedStudents() {
  if (!currentClass) return notify('Mở chi tiết lớp trước', true);
  const checked = Array.from(document.querySelectorAll('.select-stu:checked')).map(i => i.dataset.id);
  if (!checked.length) return notify('Chưa chọn sinh viên', true);
  if (!confirm(`Xóa ${checked.length} sinh viên đã chọn?`)) return;
  let deleted = 0;
  for (const sid of checked) {
    try {
      const res = await fetch(`${API_BASE_URL}/teacher/classes/${currentClass.class_id}/students/${sid}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      if (res.ok) deleted++;
    } catch (err) {
      console.error('deleteSelected error', err);
    }
  }
  notify(`Đã xóa ${deleted}/${checked.length} sinh viên (nếu có)`);
  const updated = await fetchClassDetail(currentClass.class_id);
  if (updated) {
    currentClass = updated;
    renderStudentTable();
    document.getElementById('modal-count').textContent = currentClass.students?.length ?? 0;
  }
}

// ---------- Delete class ----------
async function confirmDeleteClass() {
  if (!currentClass) return;
  if (!confirm(`Xóa lớp ${currentClass.class_name}?`)) return;
  try {
    const res = await fetch(`${API_BASE_URL}/teacher/classes/${currentClass.class_id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Xóa lớp thất bại');
    notify('Đã xóa lớp');
    closeModal();
    await fetchClasses();
  } catch (err) {
    console.error('confirmDeleteClass', err);
    notify('Xóa lớp thất bại', true);
  }
}

// ---------- Import / Export ----------
function triggerImport() {
  document.getElementById('import-file').click();
}
function importCSV(e) {
  const f = e.target.files[0];
  if (!f) return;
  const reader = new FileReader();
  reader.onload = async ev => {
    const lines = ev.target.result.split(/\r?\n/).slice(1).filter(x => x.trim());
    if (!lines.length) return notify('CSV trống', true);
    let added = 0;
    for (const l of lines) {
      const cols = l.split(',');
      const name = (cols[0] || '').trim();
      const code = (cols[1] || '').trim();
      if (!name || !code) continue;
      try {
        const res = await fetch(`${API_BASE_URL}/teacher/classes/${currentClass.class_id}/students`, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ full_name: name, student_code: code })
        });
        if (res.ok) added++;
      } catch (err) { console.error('importCSV add error', err); }
    }
    notify(`Đã import ${added}/${lines.length} SV (frontend only)`);
    const updated = await fetchClassDetail(currentClass.class_id);
    if (updated) { currentClass = updated; renderStudentTable(); document.getElementById('modal-count').textContent = currentClass.students?.length ?? 0; }
  };
  reader.readAsText(f);
}
function exportCSV() {
  if (!currentClass || !currentClass.students?.length) return notify('Không có SV để export', true);
  const lines = ['full_name,student_code', ...currentClass.students.map(s => `${s.full_name},${s.student_code}`)];
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${currentClass.class_name || 'class'}.csv`;
  a.click();
  notify('Đã xuất CSV');
}

// ---------- Select all ----------
function toggleSelectAll(cb) {
  const checked = cb.checked;
  document.querySelectorAll('.select-stu').forEach(i => i.checked = checked);
}

// ---------- Utilities ----------
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

// ---------- Init ----------
document.addEventListener('DOMContentLoaded', async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    console.error('No token found, redirect to /login');
    window.location.href = '/login';
    return;
  }

  // init dark mode & injected toggle
  initDarkModeFromStorage();
  ensureHeaderDarkToggle();

  // attach form handlers
  const form = document.getElementById('create-class-form');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('class-name').value.trim();
      const code = document.getElementById('class-code').value.trim();
      if (!name) return notify('Vui lòng nhập tên lớp', true);
      await createClass(name, code);
      form.reset();
    });
  }

  const addBtn = document.getElementById('add-student-btn');
  if (addBtn) addBtn.addEventListener('click', (e) => { e.preventDefault(); addStudentManual(); });

  // initial load
  await fetchUser();
  await fetchClasses();

  // refresh on focus
  window.addEventListener('focus', async () => {
    try { await fetchUser(); await fetchClasses(); } catch (e) { /* ignore */ }
  });

  console.log('✅ teacherHome.js initialized');
});

// Expose some functions for inline attributes
// Expose functions globally (tránh đệ quy)
window.openClassModal = openClassModal;
window.closeModal = closeModal;
window.confirmDeleteClass = confirmDeleteClass;
window.triggerImport = triggerImport;
window.importCSV = importCSV;
window.exportCSV = exportCSV;
window.toggleSelectAll = toggleSelectAll;
window.deleteStudentFromClass = deleteStudentFromClass;
window.onGradeEdit = onGradeEdit;
window.toggleDarkMode = toggleDarkMode;
window.editProfile = () => { location.href = '/editProfile'; };
window.logout = () => { localStorage.clear(); location.href = '/login'; };

