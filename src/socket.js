// socket.js

import { io } from "socket.io-client";

// Read from environment variable
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

if (!BACKEND_URL) {
  console.error("❌ No BACKEND_URL set in environment!");
}

const socket = io(BACKEND_URL, {
  autoConnect: true,
});

// Debug logs
socket.on("connect", () => {
  console.log("✅ Connected to server with ID:", socket.id);
});

socket.on("connect_error", (err) => {
  console.error("❌ Connection error:", err.message);
});

socket.on("disconnect", () => {
  console.log("⚠️ Disconnected from server");
});

export default socket;
