const bank_select = document.querySelector("#bank_select");
const card_select = document.querySelector("#card_select");
const submit = document.querySelector("#new_card_submit");
const banks_url = "https://rewardia.net/api/banks/";

async function get_auth_token() {
  const result = await chrome.storage.local.get(["authToken"]);
  return result.authToken;
}

async function get_banks() {
  const response = await fetch(banks_url);
  const banks = await response.json();

  banks.forEach((bank) => {
    const bank_selection = `<option value="${bank.bank}">${bank.bank}</option>`;

    bank_select.insertAdjacentHTML("beforeend", bank_selection);
  });

  return bank_select.value;
}

await get_banks();

async function get_cards(bank) {
  card_select.innerHTML = "<option>選擇卡片</option>";
  const cards_url = `https://rewardia.net/api/banks/${bank}/cards`;
  const response = await fetch(cards_url);
  const cards = await response.json();

  cards.forEach((card) => {
    const card_selection = `<option value="${card.id}">${card.name}</option>`;

    card_select.insertAdjacentHTML("beforeend", card_selection);
  });

  return card_select.value;
}

bank_select.addEventListener("change", async function () {
  const bank = this.value;
  await get_cards(bank);
});

submit.addEventListener("click", async function (e) {
  e.preventDefault();
  const new_card_url = `https://rewardia.net/api/users/new_card/${card_select.value}`;

  const token = await get_auth_token();
  const response = await fetch(new_card_url, {
    method: "POST",
    headers: {
      Authorization: `Token ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ card: card_select.value }),
  });
  window.location.href = "login.html";
});
