const base_url = "https://rewardia.net/";
const token_url = `${base_url}/users/api/get_token`;
const member_zone = `${base_url}/users/member`;

let loggedin = false;

// 登入相關
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
    chrome.storage.local.set({
      authToken: data.token,
      username: data.username,
      userID: data.user_id,
    });
  }
  return;
}

const login_view = document.querySelector(".login_view");
const account_content = document.querySelector(".account_content");

function return_login_view() {
  const login_view = `<div class="login_view">
        <div class="login_img"><i class="fa-solid fa-gifts"></i></div>
        <a target="_blank" href="${base_url}/sessions/login/"
          ><button class="btn login_btn">立即登入/註冊</button></a
        >
      </div>`;

  account_content.innerHTML = login_view;
}

async function return_loggedin_view(token, username, id) {
  loggedin = true;
  const loggedin_view = `<div class="user_cards"><h1>${username} 的卡片</h1></div><div><button class="btn logout_btn">登出</button></div>`;
  account_content.innerHTML = loggedin_view;

  const logout_btn = document.querySelector(".logout_btn");
  logout_btn.addEventListener("click", logout);

  await get_user_cards(token, id);
}

function logout() {
  loggedin = false;
  chrome.storage.local.remove("authToken");
  chrome.storage.local.remove("username");
  chrome.storage.local.remove("userID");
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

async function get_userID() {
  const result = await chrome.storage.local.get(["userID"]);
  return result.userID;
}

// 顯示使用者卡片相關
async function get_user_cards(token, id) {
  const user_cards_url = `${base_url}/api/users/${id}/cards/`;
  const user_cards = document.querySelector(".user_cards");
  const response = await fetch(user_cards_url, {
    headers: {
      Authorization: `Token ${token}`,
      "Content-Type": "application/json",
    },
  });
  const cards = await response.json();

  cards.forEach((card) => {
    const card_view = `<div data-id="${card.card.id}" class="card">
        <div class="card_text">
          <h2>${card.card.name}</h2>
        </div>
        <div class="delete_card">
          <button data-id="${card.card.id}" class="delete_card_btn">刪除</button>
        </div>
      </div>`;
    user_cards.insertAdjacentHTML("beforeend", card_view);
  });

  //刪除卡片相關
  const delete_btns = document.querySelectorAll(".delete_card_btn");

  delete_btns.forEach((btn) => {
    btn.addEventListener("click", async function () {
      const confirm_view = `<div class="confirm_view">
    <h1>確定要刪除卡片嗎？</h1>
    <div class="buttons">
        <a href="login.html"><button class="cancel">取消</button></a>
        <button data-id="${btn.dataset.id}" class="confirm">確認</button>
      </div></div>`;
      user_cards.innerHTML = confirm_view;
      const confirm_btn = document.querySelector(
        `.confirm[data-id='${btn.dataset.id}']`
      );

      confirm_btn.addEventListener("click", async function () {
        const card_id = btn.dataset.id;

        const delete_card_url = `${base_url}/api/users/delete_card/${card_id}/`;

        const token = await get_auth_token();
        const response = await fetch(delete_card_url, {
          method: "DELETE",
          headers: {
            Authorization: `Token ${token}`,
            "Content-Type": "application/json",
          },
        });

        window.location.href = "login.html";
      });
    });
  });

  // 若沒有卡片則顯示
  if (cards.length == 0) {
    const no_cards = `<div class="no_cards">尚未新增卡片</div>`;
    user_cards.insertAdjacentHTML("beforeend", no_cards);
  }

  // 把新增按鈕放在最下面
  const new_card_btn = `<div class="card new_card">
        <div class="card_text">
        <a href="new_card.html">
          <h2>+ 新增卡片</h2>
        </a>
        </div>
      </div>`;
  user_cards.insertAdjacentHTML("beforeend", new_card_btn);
}

const login_btn = document.querySelector(".login_btn");

// 確認登入狀態，並做出對應的事情
async function check_login_status() {
  return_login_view();
  let token = await get_auth_token();
  let username = await get_username();
  let userID = await get_userID();
  if (!token) {
    let cur_url = await get_current_url();
    if (cur_url.includes("https://rewardia.net/")) {
      await fetch_token(token_url);
      token = await get_auth_token();
      username = await get_username();
      userID = await get_userID();
    }
  }
  if (token && username) {
    loggedin = true;
    return_loggedin_view(token, username, userID);
  }
}

check_login_status();
