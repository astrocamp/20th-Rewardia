chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "open_extension") {
    chrome.action.openPopup();
  }
});
