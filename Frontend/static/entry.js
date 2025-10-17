// Hàm kiểm tra trạng thái người dùng
function checkLogin() {
    const token = localStorage.getItem("token");

    if (token) {
        // Giả sử token tồn tại nghĩa là đã đăng nhập
        window.location.href = "/home";
    } else {
        // Chưa có token -> chuyển đến trang đăng nhập
        window.location.href = "/login";
    }
}

// Chạy ngay khi trang load
window.onload = checkLogin;