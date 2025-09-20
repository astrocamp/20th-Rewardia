const base_url = "https://rewardia.net/";
const token_url = `${base_url}/users/api/get_token`;

const merchantMap = {
  momo: "momo購物",
  pchome: "pchome",
};

async function get_current_url() {
  let queryOptions = { active: true, currentWindow: true };
  const [tab] = await chrome.tabs.query(queryOptions);
  return tab.url;
}

async function get_rewards(merchant) {
  const url = `${base_url}/api/rewards/scope/${merchant}`;
  const response = await fetch(url);
  const data = await response.json();
  return data;
}

async function get_merchant_data() {
  let cur_url = await get_current_url();
  let merchant = Object.keys(merchantMap).find((key) => {
    return cur_url.includes(key);
  });

  if (merchant) {
    const data = await get_rewards(merchantMap[merchant]);
    return data;
  }
}

async function get_user_cards(token, id) {
  try {
    const user_cards_url = `${base_url}/api/users/${id}/cards/`;
    const response = await fetch(user_cards_url, {
      headers: {
        Authorization: `Token ${token}`,
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      console.error(`抓使用者卡片出現錯誤: ${response.status}`);
      return [];
    }
    const cards = await response.json();
    return cards;
  } catch (error) {
    console.error(`抓使用者卡片出現錯誤: ${error}`);
    return [];
  }
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

async function get_auth_token() {
  const result = await chrome.storage.local.get(["authToken"]);
  return result.authToken;
}

async function get_userID() {
  const result = await chrome.storage.local.get(["userID"]);
  return result.userID;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "calculate") {
    (async () => {
      const [token, userID] = await Promise.all([
        get_auth_token(),
        get_userID(),
      ]);
      const user_cards = (token, userID)
        ? await get_user_cards(token, userID)
        : [];
      const merchant_data = await get_merchant_data();
      // 取第一個，因為第一個是最大值
      sendResponse({ data: merchant_data?.[0], cards: user_cards });
    })();

    return true;
  }

  if (message.action === "get_user_cards") {
    (async () => {
      const token = await get_auth_token();
      const userID = await get_userID();
      const cards = await get_user_cards(token, userID);
      sendResponse({ data: cards });
    })();

    return true;
  }

  if (message.action === "open_loggedin") {
    chrome.action.openPopup();
    chrome.action.setIcon({
      path: "images/Rewardia-loggedin.png",
    });
  }
  if (message.action === "open_extension") {
    chrome.action.openPopup();
  }
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url.includes("rewardia.net")) {
    await fetch_token(token_url);
  }
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url.includes("rewardia.net")) {
    await fetch_token(token_url);
  }
});
