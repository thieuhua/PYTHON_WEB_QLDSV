// Load profile on DOM ready
// (the form submit handler is attached at the bottom of this file)
// Ensure user is authenticated (login.js also runs global auth checks)
if (!localStorage.getItem('token')) {
    window.location.href = '/login';
}

function makeNotif(message, isError = false, timeout = 3500) {
    const n = document.createElement('div');
    n.className = 'notification' + (isError ? ' error' : '');
    n.textContent = message;
    document.getElementById('notif-container').appendChild(n);
    setTimeout(() => n.remove(), timeout);
}

function handleError(err) {
    console.error(err);
    const msg = (err && err.message) ? err.message : 'Đã xảy ra lỗi';
    makeNotif(msg, true);
}

async function fetchProfile() {
    try {
        const res = await fetch('/api/me', { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
        if (!res.ok) throw new Error('Không thể lấy thông tin người dùng');
        const data = await res.json();

        // Fill sidebar
        document.getElementById('username').textContent = data.username || '-';
        document.getElementById('user-role').textContent = data.role || '-';
        document.getElementById('student-code-display').textContent = (data.student_profile && data.student_profile.student_code) || (data.teacher_profile && data.teacher_profile.teacher_id) || '-';
        document.getElementById('birthdate-display').textContent = (data.student_profile && data.student_profile.birthdate) || '-';

        // Fill form
        document.getElementById('fullName').value = data.full_name || '';
        document.getElementById('email').value = data.email || '';

        // Show role-specific sections
        if (data.role === 'student') {
            document.getElementById('studentFields').style.display = 'block';
            document.getElementById('teacherFields').style.display = 'none';
            if (data.student_profile) {
                document.getElementById('student-code-form').value = data.student_profile.student_code || '';
                if (data.student_profile.birthdate) document.getElementById('birthdate').value = data.student_profile.birthdate;
            }
        } else if (data.role === 'teacher') {
            document.getElementById('teacherFields').style.display = 'block';
            document.getElementById('studentFields').style.display = 'none';
            if (data.teacher_profile) {
                document.getElementById('department').value = data.teacher_profile.department || '';
                document.getElementById('title').value = data.teacher_profile.title || '';
            }
        } else {
            document.getElementById('studentFields').style.display = 'none';
            document.getElementById('teacherFields').style.display = 'none';
        }

    } catch (err) {
        handleError(err);
    }
}

async function updateProfile(body) {
    try {
        console.log("📤 Gửi dữ liệu cập nhật:", body);
        const res = await fetch('/api/me', {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const responseData = await res.json();
        console.log("📥 Response từ server:", responseData);

        if (!res.ok) {
            throw new Error(responseData.detail || 'Cập nhật thất bại');
        }

        // ✅ Cập nhật localStorage ngay lập tức
        localStorage.setItem('userInfo', JSON.stringify(responseData));
        console.log("✅ Cập nhật localStorage thành công");

        makeNotif('✅ Cập nhật hồ sơ thành công');
        await new Promise(resolve => setTimeout(resolve, 500));
        await fetchProfile();
    } catch (err) {
        console.error("❌ Lỗi cập nhật:", err);
        handleError(err);
    }
}

// ✅ Hàm đăng xuất
function logout() {
    console.log("🚪 Đang đăng xuất...");
    localStorage.removeItem("token");
    localStorage.removeItem("userInfo");
    console.log("✅ Đã xóa token");
    window.location.href = "/login";
}

document.addEventListener('DOMContentLoaded', () => fetchProfile());

// ...existing code...

document.getElementById('profileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        full_name: document.getElementById('fullName').value,
        email: document.getElementById('email').value
    };
    const np = document.getElementById('newPassword').value;
    if (np) payload.password = np;

     // role-specific - FIX ĐÂY
    const studentFieldsEl = document.getElementById('studentFields');
    const teacherFieldsEl = document.getElementById('teacherFields');

    const studentVisible = studentFieldsEl && getComputedStyle(studentFieldsEl).display !== 'none';
    const teacherVisible = teacherFieldsEl && getComputedStyle(teacherFieldsEl).display !== 'none';

    if (studentVisible) {
        const studentCodeForm = document.getElementById('student-code-form').value.trim();
        if (studentCodeForm) {
            payload.student_code = studentCodeForm;
            console.log("📝 Thêm student_code:", studentCodeForm);
        }
        const b = document.getElementById('birthdate').value;
        if (b) {
            payload.birthdate = b;
            console.log("📝 Thêm birthdate:", b);
        }
    }
     if (teacherVisible) {
        payload.department = document.getElementById('department').value || null;
        payload.title = document.getElementById('title').value || null;
    }

    await updateProfile(payload);
});