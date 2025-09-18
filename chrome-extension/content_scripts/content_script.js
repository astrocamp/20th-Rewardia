const current_host = window.location.hostname;
const current_url = window.location.href;

const merchantMap = {
  momo: "momo購物",
  pchome: "pchome",
  eslite: "誠品",
  coupang: "Coupang",
  foodpanda: "foodpanda",
  kkday: "KKday",
  klook: "Klook",
};

let merchant = Object.keys(merchantMap).find((key) => {
  return current_host.includes(key);
});

if (merchant) {
  const close_popup = sessionStorage.getItem("close_popup");

  if (!close_popup) {
    show_rewardia_popup();
  }
}

async function show_rewardia_popup() {
  const popup = document.createElement("div");
  popup.className = "rewardia_popup";
  popup.innerHTML = `<div class="popup_left">
  <div class="popup_logo"><img src="${chrome.runtime.getURL(
    "images/Rewardia_128.png"
  )}"></div>
  <div class="popup_text">偵測到信用卡，點此通知查看</div></div>
  <div class="popup_close_btn">X</div>`;
  document.body.appendChild(popup);

  const popup_left = popup.querySelector(".popup_left");
  const close_btn = popup.querySelector(".popup_close_btn");
  const rewardia_popup = document.querySelector(".rewardia_popup");

  close_btn.addEventListener("click", function () {
    popup.remove();
    sessionStorage.setItem("close_popup", "true");
  });

  // 一個可以叫插件做事情的訊息，寄到background.js
  popup_left.addEventListener("click", function () {
    chrome.runtime.sendMessage({
      action: "open_extension",
    });
    popup.remove();
  });

  setTimeout(() => {
    popup.remove();
    sessionStorage.setItem("close_popup", "true");
  }, 3000);
}

if (current_url == "https://rewardia.net/users/member/") {
  chrome.runtime.sendMessage({
    action: "open_loggedin",
  });
}

if (current_url.includes("https://rewardia.net/")) {
  const log_out_btn = document.querySelector(
    "form[action='/sessions/logout/']"
  );
  log_out_btn.addEventListener("click", function () {
    chrome.runtime.sendMessage({
      action: "log_out",
    });
  });
}

// 顯示回饋金額在momo網站相關
async function display_momo_rewards(rate, card, is_user_card) {
  const checkout_price = document.querySelector(".checkout-item");
  let price = Number(
    document
      .querySelector(".checkout-content-price.final-price")
      .textContent.trim()
      .replace(/,/g, "")
      .slice(1)
  );

  let reward = (price * (rate / 100)).toFixed(2);

  if (checkout_price) {
    const display = document.createElement("span");
    display.className = "display_rewards";
    display.innerHTML = `<img src="${chrome.runtime.getURL(
      "images/Rewardia_128.png"
    )}"><p>刷 <span>${card}</span>，最高回饋${reward}元</p>`;
    checkout_price.insertAdjacentElement("afterend", display);
    if (is_user_card) {
      const user_card_notice = document.createElement("p");
      user_card_notice.innerText = "你有這張卡！";
      display.insertAdjacentElement("beforeend", user_card_notice);
    }
  }
}

if (current_url.includes("cart")) {
  const checkout_price = document.querySelector(
    ".checkout-content-price.final-price"
  );
  if (checkout_price) {
    let last_price = 0;

    function check_price() {
      const price = Number(
        document
          .querySelector(".checkout-content-price.final-price")
          .textContent.trim()
          .replace(/,/g, "")
          .slice(1)
      );

      if (price !== last_price) {
        last_price = price;
        chrome.runtime.sendMessage(
          {
            action: "calculate",
          },
          async (response) => {
            if (!response?.data || !response?.cards) return;
            const card = response.data;
            const max_rate = Number(card.max_rate);
            const card_name = card.card.name;
            const user_cards = response.cards.map((card) => {
              return card.card.name;
            });
            const is_user_card = user_cards.includes(card_name);
            await display_momo_rewards(max_rate, card_name, is_user_card);
          }
        );
      }
    }

    setInterval(check_price, 2000);
  }
}

// 填寫信用卡資訊相關
function get_user_cards() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(
      {
        action: "get_user_cards",
      },
      (response) => {
        resolve(response.data);
      }
    );
  });
}

function display_cards(cards) {
  const credit_card_area = document.querySelector("#cardTbody");
  const price = document.querySelector("#paySumB").textContent;
  const card_selector = document.createElement("tr");
  card_selector.className = "card_selector";
  card_selector.innerHTML = `<th class="selector_head"><img src="${chrome.runtime.getURL(
    "images/Rewardia_16.png"
  )}">使用者</br>信用卡：</th><td><select id="card_select" name="card" required>
              <option>選擇卡片</option>
            </select><p class="reward_price">回饋金額：${price}</p></td>`;
  const card_select = card_selector.querySelector("#card_select");

  cards.forEach((card) => {
    const card_selection = `<option value="${card.card.id}">${card.card.name}</option>`;
    card_select.insertAdjacentHTML("beforeend", card_selection);
  });
  credit_card_area.insertAdjacentElement("beforeend", card_selector);
}

function fill_card_num(card_num) {
  const card_num_1 = document.querySelector("#cardNo_1");
  const card_num_2 = document.querySelector("#cardNo_2");
  const card_num_3_hidden = document.querySelector("#cardNo_3");
  const card_num_3 = document.querySelector("#cardNo_3_temp");
  const card_num_4 = document.querySelector("#cardNo_4");

  if (card_num_1) {
    card_num_1.addEventListener("focus", function () {});

    // card_num_1.value = 4111;
    // card_num_2.value = 1111;
    // card_num_3_hidden.value = 1111;
    // card_num_3.value = "****";
    // card_num_4.value = 1111;
  }
}

if (current_url.includes("cart.momoshop.com.tw")) {
  const observer = new MutationObserver(async (mutations) => {
    const card_num_1 = document.querySelector("#cardNo_1");
    const cards = await get_user_cards();
    if (card_num_1) {
      card_num_1.addEventListener("focus", function () {
        card_num_1.value = 4111;
        display_cards(cards);
      });
    }
    // fill_card_num();
  });
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}
