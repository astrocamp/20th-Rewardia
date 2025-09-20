const base_url = "https://rewardia.net/";
const rewards_content = document.querySelector(".rewards_content");

async function get_rewards(merchant) {
  const url = `${base_url}/api/rewards/scope/${merchant}`;

  const response = await fetch(url);
  const data = await response.json();

  return data;
}

async function get_current_url() {
  let queryOptions = { active: true, currentWindow: true };
  const [tab] = await chrome.tabs.query(queryOptions);
  return tab.url;
}

async function return_cards(merchant) {
  const cards = await get_rewards(merchant);

  const title = `<h1>${merchant} 信用卡回饋</h1>`;
  rewards_content.insertAdjacentHTML("beforeend", title);

  cards.forEach((card) => {
    let card_rate;
    if (card.min_rate && card.max_rate) {
      card_rate = `<span>${card.min_rate} - ${card.max_rate}% 回饋</span>`;
    } else if (card.min_rate == null) {
      card_rate = `<span>最高 ${card.max_rate}% 回饋</span>`;
    } else if (card.max_rate == null) {
      card_rate = `<span>最低 ${card.min_rate}% 回饋</span>`;
    }

    const card_reward = `<div class="reward">
        <div class="reward_text">
          <h2>${card.card.name}</h2>
          ${card_rate}
        </div>
      </div>`;
    rewards_content.insertAdjacentHTML("beforeend", card_reward);
  });
}

const merchantMap = {
  momo: "momo購物",
  pchome: "pchome",
  eslite: "誠品",
  coupang: "Coupang",
  foodpanda: "foodpanda",
  kkday: "KKday",
  klook: "Klook",
  ".tw": "國內",
};

async function get_merchant_cards() {
  let cur_url = await get_current_url();
  let merchant = Object.keys(merchantMap).find((key) => {
    return cur_url.includes(key);
  });

  if (cur_url.includes(merchant)) {
    await return_cards(merchantMap[merchant]);
  } else {
    await return_cards("海外");
  }
}

await get_merchant_cards();
