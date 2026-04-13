import { useState, useEffect } from 'react';
import '../../styles/layout.css';

export default function Topbar({ title, subtitle, sessionId, children }) {
  const [time, setTime] = useState('');

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setTime(
        now.toLocaleTimeString('es-BO', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="topbar">
      <div className="topbar-title">
        {subtitle && (
          <span style={{ color: 'var(--text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)', letterSpacing: 2 }}>
            {subtitle} /{' '}
          </span>
        )}
        <span>{title}</span>
      </div>

      <div className="topbar-actions">
        {children}
        {sessionId && (
          <div className="topbar-session">
            SES: {sessionId}
          </div>
        )}
        <div className="topbar-time">{time}</div>
      </div>
    </header>
  );
}
