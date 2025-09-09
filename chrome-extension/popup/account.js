const token_url = "http://localhost:8000/users/api/get-token";
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
  console.log(data);

  if (data.token) {
    chrome.storage.local.set({ authToken: data.token });
    chrome.storage.local.set({ username: data.username });
  }
  return;
}

// 第一次登入抓到token，並存取在chrome.storage

// const login_btn = document.querySelector(".login_btn");
const login_view = document.querySelector(".login_view");
const account_content = document.querySelector(".account_content");

function return_login_view() {
  const login_view = `<div class="login_view">
        <div class="login_img"><i class="fa-solid fa-gifts"></i></div>
        <a target="_blank"
          ><button class="btn login_btn">立即登入/註冊</button></a
        >
      </div>`;

  account_content.innerHTML = login_view;
}

function return_loggedin_view(username) {
  loggedin = true;
  const loggedin_view = `<div id="hidden"></div><div class="login_img"><i class="fa-solid fa-gifts"></i><span class="welcome_msg">嗨 ${username}！恭喜登入成功！</span></div><div><button class="btn logout_btn">登出</button></div>`;
  login_view.classList.add("hidden");
  account_content.innerHTML = loggedin_view;

  const logout_btn = document.querySelector(".logout_btn");

  logout_btn.addEventListener("click", function () {
    loggedin = false;
    chrome.storage.local.remove("authToken");
    chrome.storage.local.remove("username");
    return_login_view();
  });
}

async function get_auth_token() {
  const result = await chrome.storage.local.get(["authToken"]);
  return result.authToken;
}

async function get_username() {
  const result = await chrome.storage.local.get(["username"]);
  return result.username;
}

// const token = await get_auth_token();
// const username = await get_username();

// if (token) {
//   return_loggedin_view(username);
// }

if (!loggedin) {
  await fetch_token(token_url);
  const token = await get_auth_token();
  const username = await get_username();
  if (token) {
    loggedin = true;
    return_loggedin_view(username);
  }
}

// document.addEventListener("DOMContentLoaded", async function () {
// const cur_url = await get_current_url();
// console.log(cur_url);
// if (cur_url == member_zone) {
//   await fetch_token(token_url);
// }
//   const token = await get_auth_token();
//   const username = await get_username();
//   console.log(token, username);

//   if (token) {
//     return_loggedin_view(username);
//   }
// });
