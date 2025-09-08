if (window.location.hostname.includes("24h.pchome.com.tw")) {
  show_rewardia_popup();
}

function show_rewardia_popup() {
  // Simple popup for testing
  const popup = document.createElement("div");
  popup.className = "popup";
  popup.innerHTML = `<div class="header">
  <div class="logo">REWARDIA</div>
  <div class="close_btn">X</div>
  </div>
  <div class="center_img">
    <img src="${chrome.runtime.getURL("images/treasure.png")}" alt="" />
  </div>
  <div class="text">
    <button class="popup_btn">偵測到信用卡，由此詳細</button>
  </div>`;

  document.body.appendChild(popup);
  const close_btn = document.querySelector(".close_btn");
  close_btn.addEventListener("click", function () {
    popup.remove();
  });
}
