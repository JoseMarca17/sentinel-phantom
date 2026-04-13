import { useEffect, useRef, useCallback } from 'react';
import { getSocket } from '../services/socket';

export function useSocket(eventHandlers = {}) {
  const socket = getSocket();
  const handlersRef = useRef(eventHandlers);
  handlersRef.current = eventHandlers;

  useEffect(() => {
    const entries = Object.entries(handlersRef.current);
    entries.forEach(([event, handler]) => {
      socket.on(event, handler);
    });

    return () => {
      entries.forEach(([event, handler]) => {
        socket.off(event, handler);
      });
    };
  }, [socket]);

  const emit = useCallback((event, data) => {
    socket.emit(event, data);
  }, [socket]);

  const isConnected = socket.connected;

  return { emit, isConnected, socket };
}

export default useSocket;
