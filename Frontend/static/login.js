// Xử lý chuyển đổi giữa form đăng nhập và đăng ký
const container = document.getElementById("container");
const signUpButton = document.getElementById("signUp");
const signInButton = document.getElementById("signIn");

signUpButton.addEventListener("click", () => {
    container.classList.add("right-panel-active");
});

signInButton.addEventListener("click", () => {
    container.classList.remove("right-panel-active");
});

// ====== Hàm tiện ích ======
async function postData(url = "", data = {}) {
    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });

    if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `Lỗi ${res.status}`);
    }
    return res.text(); // API trả về token dạng text
}

// ====== Xử lý đăng ký ======
const registerForm = document.querySelector(".sign-up-container form");
registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();

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
        const token = await postData("/api/register", { username, password });
        localStorage.setItem("token", token);
        alert("Đăng ký thành công!");
        window.location.href = "/home";
    } catch (err) {
        alert("Lỗi đăng ký: " + err.message);
    }
});

// ====== Xử lý đăng nhập ======
const loginForm = document.querySelector(".sign-in-container form");
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const [usernameInput, passwordInput] =
        loginForm.querySelectorAll("input");

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    try {
        const token = await postData("/api/login", { username, password });
        localStorage.setItem("token", token);
        window.location.href = "/home";
    } catch (err) {
        alert("Sai tên đăng nhập hoặc mật khẩu!");
    }
});
