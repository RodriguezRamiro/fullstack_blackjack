// src/config.js

export const BACKEND_URL = process.env.NODE_ENV === "development"
  ? "http://localhost:5000"
  : "https://fullstack-blackjack.onrender.com";
