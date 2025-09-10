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

function show_rewardia_popup() {
  const popup = document.createElement("div");
  popup.className = "rewardia_popup";
  popup.innerHTML = `<div class="popup_logo"><img src="${chrome.runtime.getURL(
    "images/logo.png"
  )}"></div>
  <div class="popup_text">偵測到${5}張信用卡，點此通知查看</div>
  <div class="popup_close_btn">X</div>`;

  document.body.appendChild(popup);
  const close_btn = popup.querySelector(".popup_close_btn");
  close_btn.addEventListener("click", function () {
    popup.remove();
    sessionStorage.setItem("close_popup", "true");
  });

  setTimeout(() => {
    popup.remove();
  }, 8000);
}
