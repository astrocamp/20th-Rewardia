const token_url = "http://localhost:8000/users/api/get-token";
const member_zone = "http://localhost:8000/users/member";

async function get_current_tab() {
  let queryOptions = { active: true, currentWindow: true };
  const [tab] = await chrome.tabs.query(queryOptions);
  return tab;
}

const cur_url = await get_current_tab().then((tab) => {
  return tab.url;
});

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
  }
  const user_token = {
    token: data.token,
    username: data.username,
  };

  return user_token;
}

if (cur_url == member_zone) {
  const user_token = fetch_token(token_url);
}

const login_btn = document.querySelector(".login_btn");
const logout_btn = document.querySelector(".logout_btn");
const login_view = document.querySelector(".login_view");

async function return_loggedin_view() {
  const username = user_token.username;
  const account_content = document.querySelector(".account_content");
  console.log(account_content);
  const loggedin_view = `<div id="hidden"></div><div class="login_img"><i class="fa-solid fa-gifts"></i><span class="welcome_msg">嗨 ${username}！恭喜登入成功！</span></div><div><button class="btn logout_btn">登出</button></div>`;
  login_view.classList.add("hidden");
  account_content.innerHTML = loggedin_view;
}

chrome.storage.local.get(["authToken"], (result) => {
  const token = result.authToken;
  if (token) {
    return_loggedin_view();
  }
});

logout_btn.addEventListener("click", function () {
  chrome.storage.local.remove("authToken");
});
