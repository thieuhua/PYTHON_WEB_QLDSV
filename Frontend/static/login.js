// Xử lý chuyển đổi giữa form đăng nhập và đăng ký
console.log("🔧 login.js đang chạy...");

const container = document.getElementById("container");
const signUpButton = document.getElementById("signUp");
const signInButton = document.getElementById("signIn");

console.log("📝 Container:", container ? "CÓ" : "KHÔNG");
console.log("📝 SignUp button:", signUpButton ? "CÓ" : "KHÔNG");
console.log("📝 SignIn button:", signInButton ? "CÓ" : "KHÔNG");

if (signUpButton && signInButton) {
    signUpButton.addEventListener("click", () => {
        container.classList.add("right-panel-active");
    });

    signInButton.addEventListener("click", () => {
        container.classList.remove("right-panel-active");
    });
}

// ====== Hàm tiện ích ======
async function postData(url = "", data = {}) {
    console.log("📡 Gọi API:", url, data);
    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });

    if (!res.ok) {
        const msg = await res.text();
        console.error("❌ API Error:", msg);
        throw new Error(msg || `Lỗi ${res.status}`);
    }
    return res.json();
}

// Hàm lưu token và thông tin user
function saveAuthData(token, userData) {
    localStorage.setItem("token", token);
    localStorage.setItem("userInfo", JSON.stringify(userData));
}

// Hàm lấy token từ localStorage
function getToken() {
    return localStorage.getItem("token");
}

// Hàm thêm token vào headers
function getAuthHeaders() {
    const token = getToken();
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };
}

// ====== BẢO VỆ CLIENT-SIDE ======
async function checkAuthAndRedirect() {
    const token = getToken();
    const currentPath = window.location.pathname;
    
    console.log("=== 🔐 AUTH CHECK ===");
    console.log("📁 Current path:", currentPath);
    console.log("🔑 Token exists:", token ? "YES" : "NO");

    // Cho phép truy cập trang công cộng mà không cần auth
    const publicPaths = ['/login', '/', '/403'];
    if (publicPaths.includes(currentPath)) {
        console.log("✅ Public page - allowed");
        return;
    }

    if (!token) {
        console.log("❌ No token - redirect to login");
        window.location.href = '/login';
        return;
    }

    try {
        console.log("🔍 Checking token validity...");
        const response = await fetch("/api/me", {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error("Token không hợp lệ");
        }
        
        const userData = await response.json();
        console.log("✅ User authenticated:", userData.username);
        console.log("🎯 User role:", userData.role);
        
        // Kiểm tra quyền truy cập
        const hasAccess = hasPermission(userData.role, currentPath);
        console.log("🔐 Access granted:", hasAccess);
        
        if (!hasAccess) {
            console.log("🚫 Access denied - redirect to 403");
            window.location.href = '/403';
            return;
        }
        
        console.log("✅ Access granted - continuing...");
        
    } catch (error) {
        console.error("❌ Auth check failed:", error);
        localStorage.removeItem("token");
        localStorage.removeItem("userInfo");
        window.location.href = '/login';
    }
}

// Kiểm tra quyền truy cập - PHIÊN BẢN CHẶT CHẼ
function hasPermission(userRole, path) {
    // Định nghĩa quyền truy cập cho từng role
    const rolePermissions = {
        'student': [
            '/',            // Trang chủ
            '/student'      // Trang student
        ],
        'teacher': [
            '/',            // Trang chủ  
            '/teacher'      // Trang teacher
        ],
        'admin': [
            '/',            // Trang chủ
            '/student',     // Trang student
            '/teacher',     // Trang teacher
            '/admin'        // Trang admin
        ]
    };
    
    // Lấy danh sách paths được phép cho role này
    const allowedPaths = rolePermissions[userRole] || [];
    
    // Kiểm tra path hiện tại có trong danh sách được phép không
    const hasAccess = allowedPaths.includes(path);
    
    console.log(`🎯 PERMISSION CHECK:`);
    console.log(`   👤 User Role: ${userRole}`);
    console.log(`   📍 Requested Path: ${path}`);
    console.log(`   ✅ Allowed Paths:`, allowedPaths);
    console.log(`   🔐 Access: ${hasAccess ? 'GRANTED' : 'DENIED'}`);
    
    return hasAccess;
}

function checkLogin(token) {
    console.log("🔍 checkLogin được gọi, token:", token ? "CÓ" : "KHÔNG");
    
    if (token) {
        console.log("📡 Đang gọi API /api/me...");
        fetch("/api/me", {
            method: "GET",
            headers: getAuthHeaders()
        })
        .then(res => {
            console.log("📊 API /me status:", res.status, res.statusText);
            console.log("✅ OK?", res.ok);
            
            if (!res.ok) {
                console.error("❌ API /me failed");
                throw new Error("Token không hợp lệ hoặc đã hết hạn");
            }
            return res.json();
        })
        .then(data => {
            console.log("✅ API /me response:", data);
            saveAuthData(token, data);
            redirectByRole(data.role);
        })
        .catch(err => {
            console.error("💥 checkLogin error:", err);
            localStorage.removeItem("token");
            localStorage.removeItem("userInfo");
            alert("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại!");
            window.location.href = "/login";
        });
    } else {
        console.log("❌ Không có token trong checkLogin");
    }
}

// Hàm chuyển hướng theo role
function redirectByRole(role) {
    console.log("🎯 redirectByRole được gọi với role:", role);
    
    switch(role) {
        case "student":
            console.log("➡️ Chuyển hướng đến /student");
            window.location.href = "/student";
            break;
        case "teacher":
            console.log("➡️ Chuyển hướng đến /teacher");
            window.location.href = "/teacher";
            break;
        case "admin":
            console.log("➡️ Chuyển hướng đến /admin");
            window.location.href = "/admin";
            break;
        default:
            console.warn("⚠️ Role không xác định:", role);
            window.location.href = "/";
    }
}

// ====== HÀM ĐĂNG XUẤT ======
function logout() {
    console.log("🚪 Đang đăng xuất...");
    
    // Xóa token và user info
    localStorage.removeItem("token");
    localStorage.removeItem("userInfo");
    
    console.log("✅ Đã xóa token");
    
    // Chuyển hướng về trang login
    window.location.href = "/login";
}

// Hiển thị thông tin user
function displayUserInfo() {
    const token = getToken();
    const userInfo = localStorage.getItem("userInfo");
    
    if (token && userInfo) {
        try {
            const user = JSON.parse(userInfo);
            console.log("👋 Xin chào:", user.username, "Role:", user.role);
        } catch (e) {
            console.error("Lỗi parse userInfo:", e);
        }
    }
}

// ====== Xử lý đăng ký ======
const registerForm = document.querySelector(".sign-up-container form");
console.log("📝 Register form:", registerForm ? "CÓ" : "KHÔNG");

if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        console.log("🔄 Register form submitted");

        const [usernameInput, passwordInput, retypeInput] =
            registerForm.querySelectorAll("input");

        const username = usernameInput.value.trim();
        const password = passwordInput.value;
        const retype = retypeInput.value;

        if (password !== retype) {
            alert("Mật khẩu nhập lại không khớp!");
            return;
        }

        try {
            const result = await postData("/api/register", { username, password });
            console.log("✅ Register response:", result);
            const token = result.token;
            
            if (token) {
                localStorage.setItem("token", token);
                checkLogin(token);
            } else {
                throw new Error("Không nhận được token từ server");
            }
        } catch (err) {
            alert("Lỗi đăng ký: " + err.message);
        }
    });
}

// ====== Xử lý đăng nhập ======
const loginForm = document.querySelector(".sign-in-container form");
console.log("📝 Login form:", loginForm ? "CÓ" : "KHÔNG");

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        console.log("🔄 Login form submitted");

        const [usernameInput, passwordInput] =
            loginForm.querySelectorAll("input");

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        console.log("👤 Login attempt - Username:", username);
        console.log("🔑 Password:", password ? "***" : "RỖNG");

        try {
            const result = await postData("/api/login", { username, password });
            console.log("✅ Login response:", result);
            
            const token = result.token;
            console.log("🔐 Token:", token ? "CÓ" : "KHÔNG");
            
            if (token) {
                console.log("💾 Lưu token vào localStorage");
                localStorage.setItem("token", token);
                console.log("🔄 Gọi checkLogin...");
                checkLogin(token);
            } else {
                throw new Error("Không nhận được token từ server");
            }
        } catch (err) {
            console.error("❌ Login error:", err);
            alert("Sai tên đăng nhập hoặc mật khẩu!");
        }
    });
}

// ====== TỰ ĐỘNG KIỂM TRA ĐĂNG NHẬP KHI TẢI TRANG ======
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 DOM đã load xong");
    displayUserInfo();
    checkAuthAndRedirect(); // QUAN TRỌNG: Kiểm tra auth trên mọi trang
});

console.log("✅ login.js đã chạy xong");