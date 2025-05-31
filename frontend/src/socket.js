// socket.js
import { io } from 'socket.io-client';

const BACKEND_URL = "https://fullstack-blackjack.onrender.com";

const socket = io(BACKEND_URL, {
    withCredentials: true,
    autoConnect: true,
    transports: ['websocket'],  // optional but can improve reliability
});

export default socket;
