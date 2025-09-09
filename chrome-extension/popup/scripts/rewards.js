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

async function return_cards(merchant) {
  const cards = await get_rewards(merchant);

  cards.forEach((card) => {
    const card_reward = `<div class="reward">
        <div class="reward_text">
          <h2>${card.card.name}</h2>
          <span>最高${card.max_rate}%回饋</span>
        </div>
      </div>`;
    console.log(card_reward);
    rewards_content.insertAdjacentHTML("beforeend", card_reward);
  });
}

const cur_url = await get_current_url();

if (cur_url.includes("momo")) {
  await return_cards("momo購物");
}
