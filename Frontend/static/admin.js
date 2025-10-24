// Admin JavaScript
let allUsers = [];
let currentEditingUser = null;

// DOM Elements
const usersTableBody = document.getElementById('usersTableBody');
const searchInput = document.getElementById('searchInput');
const roleModal = document.getElementById('roleModal');
const modalUsername = document.getElementById('modalUsername');
const updateRoleBtn = document.getElementById('updateRoleBtn');
const closeModal = document.querySelector('.close');

// Load users khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
    setupEventListeners();
});

function setupEventListeners() {
    searchInput.addEventListener('input', filterUsers);
    updateRoleBtn.addEventListener('click', updateUserRole);
    closeModal.addEventListener('click', closeRoleModal);
    
    // Đóng modal khi click bên ngoài
    window.addEventListener('click', function(event) {
        if (event.target === roleModal) {
            closeRoleModal();
        }
    });
}

// Load danh sách users từ API
async function loadUsers() {
    try {
        const response = await fetch('/api/debug-all-users');
        if (!response.ok) throw new Error('Failed to fetch users');
        
        allUsers = await response.json();
        displayUsers(allUsers);
        updateStats(allUsers);
    } catch (error) {
        console.error('Error loading users:', error);
        alert('Lỗi khi tải danh sách user: ' + error.message);
    }
}

// Hiển thị users trong table
function displayUsers(users) {
    usersTableBody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>
                <span class="role-badge role-${user.role}">
                    ${getRoleDisplayName(user.role)}
                </span>
            </td>
            <td>
                <button class="btn-edit" onclick="openRoleModal('${user.username}', '${user.role}')">
                    ✏️ Phân quyền
                </button>
            </td>
        `;
        
        usersTableBody.appendChild(row);
    });
}

// Lọc users
function filterUsers() {
    const searchTerm = searchInput.value.toLowerCase();
    const filteredUsers = allUsers.filter(user => 
        user.username.toLowerCase().includes(searchTerm)
    );
    displayUsers(filteredUsers);
}

// Cập nhật thống kê
function updateStats(users) {
    const totalUsers = users.length;
    const totalStudents = users.filter(u => u.role === 'student').length;
    const totalTeachers = users.filter(u => u.role === 'teacher').length;
    const totalAdmins = users.filter(u => u.role === 'admin').length;
    
    document.getElementById('totalUsers').textContent = totalUsers;
    document.getElementById('totalStudents').textContent = totalStudents;
    document.getElementById('totalTeachers').textContent = totalTeachers;
    document.getElementById('totalAdmins').textContent = totalAdmins;
}

// Mở modal phân quyền
function openRoleModal(username, currentRole) {
    currentEditingUser = username;
    modalUsername.textContent = username;
    
    // Check radio button tương ứng với role hiện tại
    const radioButton = document.querySelector(`input[name="role"][value="${currentRole}"]`);
    if (radioButton) {
        radioButton.checked = true;
    }
    
    roleModal.style.display = 'block';
}

// Đóng modal
function closeRoleModal() {
    roleModal.style.display = 'none';
    currentEditingUser = null;
}

// Cập nhật role cho user
async function updateUserRole() {
    if (!currentEditingUser) return;
    
    const selectedRole = document.querySelector('input[name="role"]:checked');
    if (!selectedRole) {
        alert('Vui lòng chọn role!');
        return;
    }
    
    const newRole = selectedRole.value;
    
    try {
        const response = await fetch('/api/admin/update-role', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: currentEditingUser,
                new_role: newRole
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update role');
        }
        
        const result = await response.json();
        alert(result.message);
        closeRoleModal();
        loadUsers(); // Reload danh sách users
        
    } catch (error) {
        console.error('Error updating role:', error);
        alert('Lỗi khi cập nhật role: ' + error.message);
    }
}

// Chuyển đổi tên hiển thị cho role
function getRoleDisplayName(role) {
    const roleNames = {
        'student': '👨‍🎓 Student',
        'teacher': '👨‍🏫 Teacher', 
        'admin': '🛠️ Admin'
    };
    return roleNames[role] || role;
}