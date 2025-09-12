const current_host = window.location.hostname;
const current_url = window.location.href;

console.dir(window.location);

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
    "images/Rewardia.png"
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
  }, 3000);
}

if (current_url == "http://localhost:8000/users/member/") {
  chrome.runtime.sendMessage({
    action: "open_loggedin",
  });
}
