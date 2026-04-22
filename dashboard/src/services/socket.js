// services/socket.js
import { io } from 'socket.io-client';

const PI_URL = import.meta.env.VITE_PI_API_URL?.replace('/api','') || 'http://192.168.1.50:5000';

let socket = null;

export function getSocket() {
  if (!socket) {
    socket = io(PI_URL, {
      transports: ['websocket'],
      reconnectionDelay: 2000,
      reconnectionAttempts: 10,
    });
  }
  return socket;
}

export function disconnectSocket() {
  if (socket) { socket.disconnect(); socket = null; }
}