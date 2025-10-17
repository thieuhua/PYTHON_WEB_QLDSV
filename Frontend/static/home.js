let token = localStorage.getItem('token');
let userInfoData = null;
if (!token) {
    alert("Bạn chưa đăng nhập!");
    window.location.href = "/login";
} else {
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
        const userInfo = document.getElementById("user-info");
        userInfo.textContent = `Xin chào, ${data.username} (${data.role})!`;
    })
    .catch(err => {
        console.error(err);
        localStorage.removeItem("token");
        alert("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại!");
        window.location.href = "/login";
    });
}