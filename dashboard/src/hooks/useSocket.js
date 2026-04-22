// hooks/useSocket.js
import { useEffect, useRef, useState } from 'react';
import { getSocket } from '../services/socket';

export function useSocket() {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    const s = getSocket();
    socketRef.current = s;
    s.on('connect',        () => setConnected(true));
    s.on('disconnect',     () => setConnected(false));
    s.on('phantom_event',  (e) => setLastEvent(e));
    return () => {
      s.off('connect'); s.off('disconnect'); s.off('phantom_event');
    };
  }, []);

  return { connected, lastEvent, socket: socketRef.current };
}