const token_url = "http://localhost:8000/users/api/get_token";
const member_zone = "http://localhost:8000/users/member";
let loggedin = false;

async function get_current_url() {
  let queryOptions = { active: true, currentWindow: true };
  const [tab] = await chrome.tabs.query(queryOptions);
  return tab.url;
}

async function fetch_token(url) {
  const resp = await fetch(url, {
    method: "GET",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  });
  const data = await resp.json();

  if (data.token) {
    chrome.storage.local.set({ authToken: data.token });
    chrome.storage.local.set({ username: data.username });
  }
  return;
}

const login_view = document.querySelector(".login_view");
const account_content = document.querySelector(".account_content");

function return_login_view() {
  const login_view = `<div class="login_view">
        <div class="login_img"><i class="fa-solid fa-gifts"></i></div>
        <a target="_blank" href="http://localhost:8000/sessions/login/"
          ><button class="btn login_btn">立即登入/註冊</button></a
        >
      </div>`;

  account_content.innerHTML = login_view;
}

function return_loggedin_view(username) {
  loggedin = true;
  const loggedin_view = `<div id="hidden"></div><div class="login_img"><i class="fa-solid fa-gifts"></i><span class="welcome_msg">嗨 ${username}！恭喜登入成功！</span></div><div><button class="btn logout_btn">登出</button></div>`;
  // login_view.classList.add("hidden");
  account_content.innerHTML = loggedin_view;

  const logout_btn = document.querySelector(".logout_btn");
  logout_btn.addEventListener("click", logout);
}

function logout() {
  loggedin = false;
  chrome.storage.local.remove("authToken");
  chrome.storage.local.remove("username");
  return_login_view();
}

async function get_auth_token() {
  const result = await chrome.storage.local.get(["authToken"]);
  return result.authToken;
}

async function get_username() {
  const result = await chrome.storage.local.get(["username"]);
  return result.username;
}

async function check_login_status() {
  return_login_view();
  // 一開始叫先確認有沒有token
  let token = await get_auth_token();
  let username = await get_username();

  if (!token) {
    await fetch_token(token_url);
    token = await get_auth_token();
    username = await get_username();
  }
  if (token && username) {
    loggedin = true;
    return_loggedin_view(username);
  }
}

check_login_status();
