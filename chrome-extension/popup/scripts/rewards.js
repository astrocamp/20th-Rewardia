const rewards_content = document.querySelector(".rewards_content");

async function get_rewards(merchant) {
  const url = `http://localhost:8000/api/rewards/scope/${merchant}`;

  const response = await fetch(url);
  const data = await response.json();

  return data;
}

async function get_current_url() {
  let queryOptions = { active: true, currentWindow: true };
  const [tab] = await chrome.tabs.query(queryOptions);
  return tab.url;
}

let card_count;

async function return_cards(merchant) {
  const cards = await get_rewards(merchant);

  const title = `<h1>${merchant}信用卡回饋</h1>`;
  rewards_content.insertAdjacentHTML("beforeend", title);

  cards.forEach((card) => {
    let card_reward;
    if (card.min_rate && card.max_rate) {
      card_reward = `<div class="reward">
        <div class="reward_text">
          <h2>${card.card.name}</h2>
          <span>最高 ${card.max_rate}% 回饋</span>
          <span>最低 ${card.min_rate}% 回饋</span>
        </div>
      </div>`;
    } else if (card.min_rate == null) {
      card_reward = `<div class="reward">
        <div class="reward_text">
          <h2>${card.card.name}</h2>
          <span>最高 ${card.max_rate}% 回饋</span>
        </div>
      </div>`;
    } else if (card.max_rate == null) {
      card_reward = `<div class="reward">
        <div class="reward_text">
          <h2>${card.card.name}</h2>
          <span>最低 ${card.min_rate}% 回饋</span>
        </div>
      </div>`;
    }
    rewards_content.insertAdjacentHTML("beforeend", card_reward);
  });
}

const cur_url = await get_current_url();

if (cur_url.includes("momo")) {
  await return_cards("momo購物");
} else if (cur_url.includes("pchome")) {
  await return_cards("pchome");
} else if (cur_url.includes("tw")) {
  await return_cards("國內");
} else {
  await return_cards("海外");
}
