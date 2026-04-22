// components/layout/Topbar.jsx
import { useState, useEffect } from 'react';
import { useSocket } from '../../hooks/useSocket';
import { nowStr } from '../../utils/time';
import { mockSession } from '../../services/mockData';

const PAGE_LABELS = {
  overview: 'Overview', alerts: 'Alertas de Seguridad',
  devices: 'Dispositivos Detectados', events: 'Log de Eventos',
  modules: 'Control de Módulos', reports: 'Reportes Forenses',
};

export default function Topbar({ page, onMenuClick }) {
  const { connected, lastEvent } = useSocket();
  const [clock, setClock] = useState(nowStr());

  useEffect(() => {
    const t = setInterval(() => setClock(nowStr()), 1000);
    return () => clearInterval(t);
  }, []);

  const sid = mockSession.id.slice(0,8).toUpperCase();

  return (
    <header className="topbar">
      <button className="hamburger" onClick={onMenuClick}>☰</button>

      <div>
        <div className="topbar-title">{PAGE_LABELS[page] || page}</div>
        <div className="topbar-path" style={{ fontSize:'0.62rem' }}>
          SENTINEL PHANTOM / {page.toUpperCase()}
        </div>
      </div>

      <div className="topbar-right">
        {lastEvent && (
          <div style={{ fontSize:'0.65rem', color:'var(--blue-bright)', maxWidth:200, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
            ● {lastEvent.topic}
          </div>
        )}
        <div className="topbar-clock">{clock}</div>
        <div className="topbar-session">SID:{sid}</div>
        <div style={{ display:'flex', alignItems:'center', gap:5, fontSize:'0.68rem' }}>
          <div style={{ width:6, height:6, borderRadius:'50%', background: connected ? 'var(--teal)' : 'var(--red)' }} />
          <span style={{ color: connected ? 'var(--teal)' : 'var(--red)' }}>
            {connected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
      </div>
    </header>
  );
}