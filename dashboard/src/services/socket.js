import { io } from 'socket.io-client';

const PI_WS_URL = import.meta.env.VITE_PI_API_URL || 'http://192.168.1.100:5000';

let socket = null;

export const getSocket = () => {
  if (!socket) {
    socket = io(PI_WS_URL, {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
    });

    socket.on('connect', () => {
      console.log('[WS] Connected to Pi:', socket.id);
    });

    socket.on('disconnect', (reason) => {
      console.warn('[WS] Disconnected:', reason);
    });

    socket.on('connect_error', (err) => {
      console.error('[WS] Connection error:', err.message);
    });
  }
  return socket;
};

export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};

export default getSocket;
