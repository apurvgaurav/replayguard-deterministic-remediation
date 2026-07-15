// Mobile/backend example: hardcoded API key risk.
// This is an example input that ReplayGuard-style remediation could verify.

const API_KEY = "live_mobile_prod_key_123";

fetch("https://api.example.com/payments", {
  method: "POST",
  headers: {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    amount: 100,
    currency: "USD"
  })
});
