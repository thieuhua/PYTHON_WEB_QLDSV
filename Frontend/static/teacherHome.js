// teacherHome.js – phiên bản dùng dữ liệu động qua API

// ====== Thiết lập chung ======
let teacherClasses = [];
let currentClass = null;

// ====== Hàm tiện ích ======
function getToken() {
  return localStorage.getItem("token");
}

function getAuthHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${getToken()}`
  };
}

function notify(msg, type = "success") {
  const c = document.getElementById("notif-container");
  if (!c) return;
  const n = document.createElement("div");
  n.className = "notification" + (type === "error" ? " error" : "");
  n.textContent = msg;
  c.appendChild(n);
  setTimeout(() => { try { n.remove(); } catch (e) {} }, 3000);
}

function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ====== API GỌI TỪ BACKEND ======
async function fetchClasses() {
  try {
    const res = await fetch("/api/teacher/classes", { headers: getAuthHeaders() });
    if (!res.ok) throw new Error("Không tải được danh sách lớp");
    teacherClasses = await res.json();
    renderClassCards();
  } catch (err) {
    console.error(err);
    notify("Không tải được danh sách lớp", "error");
  }
}

async function createClass(name, year, semester) {
  try {
    const body = { class_name: name, year, semester };
    const res = await fetch("/api/teacher/classes", {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error("Tạo lớp thất bại");
    notify("✅ Tạo lớp thành công");
    await fetchClasses();
  } catch (err) {
    console.error(err);
    notify("Không thể tạo lớp", "error");
  }
}

async function fetchClassDetail(classId) {
  try {
    const res = await fetch(`/api/teacher/classes/${classId}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Không tải được chi tiết lớp");
    currentClass = await res.json();
    renderStudentTable();
  } catch (err) {
    console.error(err);
    notify("Không tải được dữ liệu lớp", "error");
  }
}

async function addStudentToClass(full_name, student_code) {
  try {
    const body = { full_name, student_code };
    const res = await fetch(`/api/teacher/classes/${currentClass.class_id}/students`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error("Không thêm được sinh viên");
    notify("✅ Thêm sinh viên thành công");
    await fetchClassDetail(currentClass.class_id);
  } catch (err) {
    console.error(err);
    notify("Không thể thêm sinh viên", "error");
  }
}

async function updateStudentGrade(student_id, field, value) {
  try {
    const body = [{ student_id, subject: field, score: value }];
    const res = await fetch(`/api/teacher/classes/${currentClass.class_id}/grades`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error("Không thể cập nhật điểm");
    notify("✅ Cập nhật điểm thành công");
    await fetchClassDetail(currentClass.class_id);
  } catch (err) {
    console.error(err);
    notify("Cập nhật điểm thất bại", "error");
  }
}

async function deleteStudentFromClass(student_id) {
  if (!confirm("Xóa sinh viên này khỏi lớp?")) return;
  try {
    const res = await fetch(`/api/teacher/classes/${currentClass.class_id}/students/${student_id}`, {
      method: "DELETE",
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Xóa thất bại");
    notify("🗑️ Đã xóa sinh viên");
    await fetchClassDetail(currentClass.class_id);
  } catch (err) {
    console.error(err);
    notify("Không thể xóa sinh viên", "error");
  }
}

// ====== HIỂN THỊ LỚP ======
function renderClassCards() {
  const grid = document.getElementById("classes-grid");
  if (!grid) return;
  if (!teacherClasses.length) {
    grid.innerHTML = `<div class="create-class-form" style="padding:1rem;"><em>Chưa có lớp học. Hãy tạo lớp mới.</em></div>`;
    return;
  }
  grid.innerHTML = teacherClasses.map(c => `
    <div class="class-card" data-id="${c.class_id}" onclick="openClassModal('${c.class_id}')">
      <h3>${escapeHtml(c.class_name)}</h3>
      <div class="class-meta"><strong>Năm học:</strong> ${c.year} - Học kỳ ${c.semester}</div>
    </div>
  `).join("");
}

// ====== MODAL CHI TIẾT LỚP ======
async function openClassModal(classId) {
  await fetchClassDetail(classId);
  const cls = currentClass;
  if (!cls) return;

  document.getElementById("modal-class-name").textContent = cls.class_name;
  document.getElementById("modal-class-code").textContent = cls.class_id;
  document.getElementById("modal-count").textContent = cls.students?.length || 0;
  document.getElementById("modal-max").textContent = cls.max_students || "-";
  document.getElementById("student-name").value = "";
  document.getElementById("student-id").value = "";
  document.getElementById("class-modal").classList.remove("hidden");
}

function closeModal() {
  currentClass = null;
  document.getElementById("class-modal").classList.add("hidden");
}

// ====== HIỂN THỊ SINH VIÊN ======
function renderStudentTable() {
  const tbody = document.getElementById("student-tbody");
  if (!tbody) return;
  const cls = currentClass;
  if (!cls || !cls.students?.length) {
    tbody.innerHTML = `<tr><td colspan="9"><em>Chưa có sinh viên trong lớp.</em></td></tr>`;
    return;
  }

  tbody.innerHTML = cls.students.map((s, idx) => {
    const att = s.grades?.attendance ?? "";
    const mid = s.grades?.mid ?? "";
    const fin = s.grades?.final ?? "";
    const avg = (att || mid || fin)
      ? ((Number(att)*0.2 + Number(mid)*0.3 + Number(fin)*0.5).toFixed(1))
      : "-";
    return `
      <tr data-stu-id="${s.student_id}">
        <td>${idx + 1}</td>
        <td>${escapeHtml(s.full_name)}</td>
        <td>${escapeHtml(s.student_code)}</td>
        <td><input class="input-grade" data-field="attendance" value="${att}" onchange="onGradeEdit('${s.student_id}', this)"></td>
        <td><input class="input-grade" data-field="mid" value="${mid}" onchange="onGradeEdit('${s.student_id}', this)"></td>
        <td><input class="input-grade" data-field="final" value="${fin}" onchange="onGradeEdit('${s.student_id}', this)"></td>
        <td>${avg}</td>
        <td><button class="create-btn small danger" onclick="deleteStudentFromClass('${s.student_id}')">Xóa</button></td>
      </tr>`;
  }).join("");
}

// ====== SỰ KIỆN ======
function onGradeEdit(studentId, inputElem) {
  const field = inputElem.getAttribute("data-field");
  const val = inputElem.value.trim();
  const num = val === "" ? "" : Number(val);
  if (num === "" || isNaN(num)) return;
  const clamped = Math.max(0, Math.min(10, Math.round(num * 10) / 10));
  inputElem.value = clamped;
  updateStudentGrade(studentId, field, clamped);
}

document.addEventListener("DOMContentLoaded", () => {
  // Nạp danh sách lớp
  fetchClasses();

  const form = document.getElementById("create-class-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const name = document.getElementById("class-name").value.trim();
      const year = new Date().getFullYear();
      const semester = 1;
      if (!name) return notify("Tên lớp không được để trống", "error");
      createClass(name, year, semester);
      form.reset();
    });
  }

  const addBtn = document.getElementById("add-student-btn");
  if (addBtn) {
    addBtn.addEventListener("click", (ev) => {
      ev.preventDefault();
      const name = document.getElementById("student-name").value.trim();
      const code = document.getElementById("student-id").value.trim();
      if (!name || !code) return notify("Vui lòng nhập đủ họ tên và mã SV", "error");
      addStudentToClass(name, code);
    });
  }
});

// ====== ĐĂNG XUẤT ======
function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("userInfo");
  window.location.href = "/login";
}
