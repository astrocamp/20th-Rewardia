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
  const url = `https://rewardia.net/api/rewards/scope/${merchant}`;
  const response = await fetch(url);
  const data = await response.json();
  return data;
}

async function get_merchant_data() {
  let cur_url = await get_current_url();
  let merchant = Object.keys(merchantMap).find((key) => {
    return cur_url.includes(key);
  });

  if (cur_url.includes(merchant)) {
    const data = await get_rewards(merchantMap[merchant]);
    return data;
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "calculate") {
    (async () => {
      const merchant_data = await get_merchant_data();
      // 取第一個，因為第一個是最大值
      sendResponse({ data: merchant_data[0] });
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
