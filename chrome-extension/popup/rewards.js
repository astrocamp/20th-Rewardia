const get_rewards = "http://localhost:8000/users/api/get_rewards";

const response = await fetch(get_rewards);
const data = await response.json();

console.log(data);
