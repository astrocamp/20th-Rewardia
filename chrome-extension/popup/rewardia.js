const token_url = "http://localhost:8000/users/api/get-token";

await fetch(token_url, {
  method: "GET",
  credentials: "include",
  header: {
    "Content-Type": "application/json",
  },
})
  .then((resp) => resp.json())
  .then((data) => {
    console.log(data);
    if (data.token) {
      chrome.storage.local.set({ authToken: data.token });
    } else {
      chrome.storage.local.remove("authToken");
    }
  });
