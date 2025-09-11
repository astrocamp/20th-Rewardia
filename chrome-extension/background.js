chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "open_loggedin") {
    chrome.action.openPopup();
    chrome.action.setIcon({
      path: "images/Rewardia-loggedin.png",
    });
  }
  if (message.action === "open_extension") {
    chrome.action.openPopup();
  }
});
