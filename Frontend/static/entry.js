// Hàm kiểm tra trạng thái người dùng
function checkLogin() {
    const token = localStorage.getItem("token");
    let userInfoData = null;
    if (token) {
        fetch("/api/me", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        })
        .then(res => {
            if (!res.ok) throw new Error("Token không hợp lệ hoặc đã hết hạn");
            return res.json();
        })
        .then(data => {
            userInfoData = data;
            if (data.role == "student"){
                window.location.href = "/student";
            }
            else if (data.role == "teacher"){
                window.location.href = "/teacher";
            }
        })
        .catch(err => {
            console.error(err);
            localStorage.removeItem("token");
            alert("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại!");
            window.location.href = "/login";
        });
    } else {
        // Chưa có token -> chuyển đến trang đăng nhập
        window.location.href = "/login";
    }
}

// Chạy ngay khi trang load
window.onload = checkLogin;