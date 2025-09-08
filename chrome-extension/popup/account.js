const token_url = "http://localhost:8000/users/api/get-token";
const member_zone = "http://localhost:8000/users/member";

async function get_current_url() {
  let queryOptions = { active: true, currentWindow: true };
  const [tab] = await chrome.tabs.query(queryOptions);
  return tab.url;
}

const cur_url = await get_current_url();

async function fetch_token(url) {
  const resp = await fetch(url, {
    method: "GET",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  });
  const data = await resp.json();
  const user_token = {
    token: data.token,
    username: data.username,
  };
  if (data.token) {
    chrome.storage.local.set({ authToken: user_token });
  }

  return user_token;
}

// 第一次登入抓到token，並存取在chrome.storage
if (cur_url == member_zone) {
  await fetch_token(token_url);
}

const login_btn = document.querySelector(".login_btn");
const login_view = document.querySelector(".login_view");

function return_loggedin_view(username) {
  const account_content = document.querySelector(".account_content");
  const loggedin_view = `<div id="hidden"></div><div class="login_img"><i class="fa-solid fa-gifts"></i><span class="welcome_msg">嗨 ${username}！恭喜登入成功！</span></div><div><button class="btn logout_btn">登出</button></div>`;
  login_view.classList.add("hidden");
  account_content.innerHTML = loggedin_view;

  const logout_btn = document.querySelector(".logout_btn");

  logout_btn.addEventListener("click", function () {
    chrome.storage.local.remove("authToken");
  });
}

async function get_auth_token() {
  await chrome.storage.local.get(["authToken"], (result) => {
    const user_token = result.authToken;
    return user_token;
  });
}

document.addEventListener("DOMContentLoaded", async function () {
  const token = await get_auth_token().token;
  const username = await get_auth_token().username;

  if (token) {
    return_loggedin_view(username);
  }
});
