const bank_select = document.querySelector("#bank_select");
const card_select = document.querySelector("#card_select");
const banks_url = "http://localhost:8000/api/banks/";

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
  const cards_url = `http://localhost:8000/api/${bank}/cards`;
  const response = await fetch(cards_url);
  const cards = await response.json();

  cards.forEach((card) => {
    const card_selection = `<option value="${card.name}">${card.name}</option>`;

    card_select.insertAdjacentHTML("beforeend", card_selection);
  });

  return card_select.value;
}

bank_select.addEventListener("change", async function () {
  const bank = await get_banks();
  await get_cards(bank);
});
