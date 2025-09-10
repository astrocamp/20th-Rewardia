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
  // Simple popup for testing
  const popup = document.createElement("div");
  popup.className = "rewardia_popup";
  popup.innerHTML = `<div class="popup_header">
  <div class="popup_logo">REWARDIA</div>
  <div class="popup_close_btn">X</div>
  </div>
  <div class="popup_center_img">
    <img src="${chrome.runtime.getURL("images/treasure.png")}" alt="" />
  </div>
  <div class="popup_text">
    <button class="popup_btn">偵測到信用卡，由此詳細</button>
  </div>`;

  document.body.appendChild(popup);
  const close_btn = popup.querySelector(".popup_close_btn");
  close_btn.addEventListener("click", function () {
    popup.remove();
    sessionStorage.setItem("close_popup", "true");
  });
}
