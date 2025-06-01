// socket.js


import { io } from 'socket.io-client';
import { BACKEND_URL } from './config';

const socket = io(BACKEND_URL, {
  withCredentials: true,
  autoConnect: true,
  transports: ['websocket'],
});

export default socket;
