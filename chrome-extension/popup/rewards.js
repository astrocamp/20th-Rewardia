async function get_rewards(merchant) {
  const url = `http://localhost:8000/api/rewards/${merchant}`;

  const response = await fetch(get_rewards);
  const data = await response.json();

  return data;
}
