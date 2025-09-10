const current_host = window.location.hostname;

if (
  current_host == "24h.pchome.com.tw" ||
  current_host == "www.momoshop.com.tw"
) {
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
    "images/logo.png"
  )}"></div>
  <div class="popup_text">偵測到信用卡，點此通知查看</div></div>
  <div class="popup_close_btn">X</div>`;
  document.body.appendChild(popup);

  const close_btn = popup.querySelector(".popup_close_btn");
  const rewardia_popup = document.querySelector(".rewardia_popup");
  console.log(rewardia_popup);

  close_btn.addEventListener("click", function () {
    popup.remove();
    sessionStorage.setItem("close_popup", "true");
  });

  // 一個可以叫插件做事情的訊息，寄到background.js
  rewardia_popup.addEventListener("click", function () {
    chrome.runtime.sendMessage({
      action: "open_extension",
    });
    popup.remove();
  });

  setTimeout(() => {
    popup.remove();
  }, 8000);
}
