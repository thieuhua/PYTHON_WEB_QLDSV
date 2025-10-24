// Hàm kiểm tra trạng thái người dùng
function checkLogin() {
    console.log("🔍 entry.js: Bắt đầu kiểm tra login...");
    
    const token = localStorage.getItem("token");
    console.log("🔑 Token:", token ? "CÓ" : "KHÔNG");
    
    if (token) {
        console.log("📡 Đang gọi API /api/me...");
        fetch("/api/me", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        })
        .then(res => {
            console.log("📊 API status:", res.status);
            if (!res.ok) throw new Error("Token không hợp lệ hoặc đã hết hạn");
            return res.json();
        })
        .then(data => {
            console.log("✅ User data:", data);
            
            // Redirect theo role
            if (data.role == "student"){
                console.log("🎓 Redirect đến /student");
                window.location.href = "/student";
            }
            else if (data.role == "teacher"){
                console.log("👨‍🏫 Redirect đến /teacher");
                window.location.href = "/teacher";
            }
            else if (data.role == "admin"){
                console.log("🛠️ Redirect đến /admin");
                window.location.href = "/admin";
            }
            else {
                console.warn("⚠️ Role không xác định:", data.role);
                window.location.href = "/login";
            }
        })
        .catch(err => {
            console.error("❌ Lỗi:", err);
            localStorage.removeItem("token");
            alert("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại!");
            window.location.href = "/login";
        });
    } else {
        console.log("❌ Không có token, redirect đến login");
        window.location.href = "/login";
    }
}

// Chạy ngay khi trang load
window.onload = checkLogin;