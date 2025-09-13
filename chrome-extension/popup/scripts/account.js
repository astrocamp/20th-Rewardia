const token_url = "http://localhost:8000/users/api/get_token";
const member_zone = "http://localhost:8000/users/member";
const user_cards_url = "http://localhost:8000/api/users/cards/";
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

async function return_loggedin_view(token, username) {
  loggedin = true;
  const loggedin_view = `<div class="user_cards"><h1>${username} 的卡片</h1></div><div><button class="btn logout_btn">登出</button></div>`;
  account_content.innerHTML = loggedin_view;

  const logout_btn = document.querySelector(".logout_btn");
  logout_btn.addEventListener("click", logout);

  await get_user_cards(token);
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

async function get_user_cards(token) {
  const user_cards = document.querySelector(".user_cards");
  const response = await fetch(user_cards_url, {
    headers: {
      Authorization: `Token ${token}`,
    },
  });
  const cards = await response.json();

  cards.forEach((card) => {
    const card_view = `<div class="card">
        <div class="card_text">
          <h2>${card.card.name}</h2>
        </div>
      </div>`;
    user_cards.insertAdjacentHTML("beforeend", card_view);
  });

  if (cards.length == 0) {
    const no_cards = `<div class="no_cards">尚未新增卡片</div>`;
    user_cards.insertAdjacentHTML("beforeend", no_cards);
  }

  const new_card_btn = `<div class="card new_card">
        <div class="card_text">
        <a href="new_card.html">
          <h2>+ 新增卡片</h2>
        </a>
        </div>
      </div>`;
  user_cards.insertAdjacentHTML("beforeend", new_card_btn);
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
    return_loggedin_view(token, username);
  }
}

check_login_status();
