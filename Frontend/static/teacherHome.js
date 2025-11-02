// teacherHome.js – FIXED VERSION - Cập nhật điểm và hiển thị đúng

// ====== Thiết lập chung ======
let teacherClasses = [];
let currentClass = null;

// ✅ THÊM MAPPING GIỮA FRONTEND VÀ BACKEND
const FIELD_MAPPING = {
  'attendance': 'attendance',
  'mid': 'mid',
  'final': 'final'
};

const DISPLAY_MAPPING = {
  'attendance': 'Chuyên Cần',
  'mid': 'Giữa Kì',
  'final': 'Cuối Kì'
};

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

async function createClass(name, year, semester, maxStudents) {
  try {
    const body = {
      class_name: name,
      year,
      semester,
      max_students: maxStudents || 50  // Gửi max_students, mặc định 50
    };
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

    console.log("📊 Class detail loaded:", currentClass); // Debug log

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

// ✅ FIXED - Gửi đúng format và reload data
async function updateStudentGrade(student_id, field, value) {
  try {
    const body = [{
      student_id: parseInt(student_id),
      class_id: currentClass.class_id,
      subject: field, // ✅ Gửi đúng tên field: "attendance", "mid", "final"
      score: parseFloat(value)
    }];

    console.log("📤 Sending grade update:", body);

    const res = await fetch(`/api/teacher/classes/${currentClass.class_id}/grades`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      console.error("❌ Error response:", errorData);
      throw new Error(errorData.detail || "Không thể cập nhật điểm");
    }

    const result = await res.json();
    console.log("✅ Grade update response:", result);

    notify("✅ Cập nhật điểm thành công");

    // ✅ RELOAD data để hiển thị điểm mới
    await fetchClassDetail(currentClass.class_id);

  } catch (err) {
    console.error("❌ Grade update error:", err);
    notify(`Cập nhật điểm thất bại: ${err.message}`, "error");
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

// ====== XÓA LỚP HỌC ======
async function confirmDeleteClass() {
  if (!currentClass) {
    notify("Không tìm thấy thông tin lớp học", "error");
    return;
  }

  const studentCount = currentClass.students?.length || 0;
  let message = `Bạn có chắc chắn muốn xóa lớp "${currentClass.class_name}"?`;

  if (studentCount > 0) {
    message += `\n\n⚠️ Lớp này có ${studentCount} sinh viên. Tất cả dữ liệu liên quan (sinh viên, điểm số) sẽ bị xóa!`;
  }

  if (!confirm(message)) return;

  await deleteClass(currentClass.class_id);
}

async function deleteClass(classId) {
  try {
    const res = await fetch(`/api/teacher/classes/${classId}`, {
      method: "DELETE",
      headers: getAuthHeaders()
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Không thể xóa lớp");
    }

    notify("✅ Đã xóa lớp học thành công");
    closeModal();
    await fetchClasses();
  } catch (err) {
    console.error(err);
    notify(`Xóa lớp thất bại: ${err.message}`, "error");
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
  document.getElementById("modal-class-join-code").textContent =cls.join_code;
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

// ✅ FIXED - Đọc đúng structure grades từ backend
function renderStudentTable() {
  const tbody = document.getElementById("student-tbody");
  if (!tbody) return;
  const cls = currentClass;

  if (!cls || !cls.students?.length) {
    tbody.innerHTML = `<tr><td colspan="8"><em>Chưa có sinh viên trong lớp.</em></td></tr>`;
    return;
  }

  console.log("📋 Rendering students:", cls.students); // Debug log

  tbody.innerHTML = cls.students.map((s, idx) => {
    // ✅ Đọc đúng từ s.grades (object với keys: attendance, mid, final)
    const grades = s.grades || {};
    const att = grades.attendance ?? "";
    const mid = grades.mid ?? "";
    const fin = grades.final ?? "";

    // Tính điểm trung bình
    const avg = (att !== "" && mid !== "" && fin !== "")
      ? ((Number(att) * 0.2 + Number(mid) * 0.3 + Number(fin) * 0.5).toFixed(1))
      : "-";

    console.log(`Student ${s.student_code}: att=${att}, mid=${mid}, fin=${fin}, avg=${avg}`);

    return `
      <tr data-stu-id="${s.student_id}">
        <td>${idx + 1}</td>
        <td>${escapeHtml(s.full_name)}</td>
        <td>${escapeHtml(s.student_code)}</td>
        <td><input class="input-grade" data-field="attendance" value="${att}" onchange="onGradeEdit('${s.student_id}', this)"></td>
        <td><input class="input-grade" data-field="mid" value="${mid}" onchange="onGradeEdit('${s.student_id}', this)"></td>
        <td><input class="input-grade" data-field="final" value="${fin}" onchange="onGradeEdit('${s.student_id}', this)"></td>
        <td><strong>${avg}</strong></td>
        <td><button class="create-btn small danger" onclick="deleteStudentFromClass('${s.student_id}')">Xóa</button></td>
      </tr>`;
  }).join("");
}

// ✅ FIXED - Validation và gửi đúng field name
function onGradeEdit(studentId, inputElem) {
  const field = inputElem.getAttribute("data-field"); // "attendance", "mid", hoặc "final"
  const val = inputElem.value.trim();

  // Cho phép xóa điểm (để trống)
  if (val === "") {
    notify("Điểm đã bị xóa", "error");
    return;
  }

  const num = Number(val);

  // Validate
  if (isNaN(num)) {
    notify("Vui lòng nhập số hợp lệ", "error");
    inputElem.value = "";
    return;
  }

  if (num < 0 || num > 10) {
    notify("Điểm phải trong khoảng 0-10", "error");
    inputElem.value = "";
    return;
  }

  // Làm tròn 1 chữ số thập phân
  const clamped = Math.round(num * 10) / 10;
  inputElem.value = clamped;

  console.log(`🔄 Updating grade: student=${studentId}, field=${field}, value=${clamped}`);

  // ✅ Gọi API với field name đúng
  updateStudentGrade(studentId, field, clamped);
}

// ====== IMPORT/EXPORT CSV ======
function triggerImport() {
  if (!currentClass) {
    notify("Vui lòng mở lớp học trước", "error");
    return;
  }
  document.getElementById("import-file").click();
}

async function importCSV(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (!file.name.endsWith('.csv')) {
    notify("Vui lòng chọn file CSV", "error");
    return;
  }

  if (!currentClass) {
    notify("Vui lòng mở lớp học trước", "error");
    return;
  }

  try {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`/api/teacher/classes/${currentClass.class_id}/import`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${getToken()}`
      },
      body: formData
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Import thất bại");
    }

    const result = await res.json();

    // Show detailed result
    let message = `✅ Import thành công: ${result.success_count} sinh viên`;
    if (result.error_count > 0) {
      message += `\n⚠️ Có ${result.error_count} lỗi`;
      if (result.errors && result.errors.length > 0) {
        message += ":\n" + result.errors.slice(0, 5).join("\n");
        if (result.errors.length > 5) {
          message += `\n... và ${result.errors.length - 5} lỗi khác`;
        }
      }
    }

    alert(message);

    // Reload class detail
    await fetchClassDetail(currentClass.class_id);

    // Clear file input
    event.target.value = '';

  } catch (err) {
    console.error(err);
    notify(`Import thất bại: ${err.message}`, "error");
    event.target.value = '';
  }
}

async function exportCSV() {
  console.log("🔍 Export CSV clicked");

  if (!currentClass) {
    console.error("❌ currentClass is null");
    notify("Vui lòng mở lớp học trước", "error");
    return;
  }

  console.log("📊 Current class:", currentClass);
  console.log("🔑 Token:", getToken() ? "Present" : "Missing");

  try {
    const url = `/api/teacher/classes/${currentClass.class_id}/export`;
    console.log("📤 Fetching:", url);

    const res = await fetch(url, {
      headers: getAuthHeaders()
    });

    console.log("📊 Response status:", res.status);
    console.log("📊 Response headers:", Object.fromEntries(res.headers.entries()));

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      console.error("❌ Export failed:", errorData);
      throw new Error(errorData.detail || "Export thất bại");
    }

    // Get filename from Content-Disposition header
    const contentDisposition = res.headers.get('Content-Disposition');
    let filename = 'students.csv';
    if (contentDisposition) {
      const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }
    console.log("📄 Filename:", filename);

    // Download file
    const blob = await res.blob();
    console.log("📄 Blob size:", blob.size, "bytes");
    console.log("📄 Blob type:", blob.type);

    const url2 = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url2;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url2);
    document.body.removeChild(a);

    console.log("✅ Export successful");
    notify("✅ Export thành công");

  } catch (err) {
    console.error("❌ Export error:", err);
    notify(`Export thất bại: ${err.message}`, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  // Nạp danh sách lớp
  fetchClasses();

  const form = document.getElementById("create-class-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const name = document.getElementById("class-name").value.trim();
      const maxStudents = parseInt(document.getElementById("max-students").value) || 50;
      const year = new Date().getFullYear();
      const semester = 1;
      if (!name) return notify("Tên lớp không được để trống", "error");
      if (maxStudents < 1 || maxStudents > 200) {
        return notify("Số lượng tối đa phải từ 1 đến 200", "error");
      }
      createClass(name, year, semester, maxStudents);
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

// ====== CHỈNH SỬA THÔNG TIN ======
function editProfile() {
  console.log("✏️ Chuyển hướng tới trang chỉnh sửa thông tin...");
  window.location.href = "/editProfile";
}

// ====== CẬP NHẬT REAL-TIME KHI QUAY LẠI =====
window.addEventListener('focus', async () => {
  console.log("🔄 Trang được focus, cập nhật thông tin...");
  await fetchClasses();
});

// ===== CẬP NHẬT REAL-TIME KHI localStorage THAY ĐỔI =====
window.addEventListener('storage', async (e) => {
  if (e.key === 'userInfo') {
    console.log("📝 localStorage userInfo thay đổi, cập nhật giao diện...");
    try {
      const updatedUser = JSON.parse(e.newValue);
      // Update sidebar nếu có
      const userNameEl = document.querySelector('.teacher-name');
      if (userNameEl && updatedUser.full_name) {
        userNameEl.textContent = updatedUser.full_name;
      }
    } catch (err) {
      console.error("❌ Lỗi parse userInfo:", err);
    }
  }
});

