// pages/EventsPage.jsx
import { useState, useEffect } from 'react';
import { useEvents } from '../hooks/usePiData';
import { useSocket } from '../hooks/useSocket';
import { fmtTime, fmtRelative } from '../utils/time';

export default function EventsPage() {
  const { data, refetch } = useEvents();
  const { lastEvent, connected } = useSocket();
  const [liveQueue, setLiveQueue] = useState([]);
  const [mod, setMod]     = useState('ALL');
  const [search, setSearch] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);

  const events = Array.isArray(data) ? data : [];
  const modules = ['ALL', ...new Set(events.map(e => e.module))];

  useEffect(() => {
    if (!lastEvent) return;
    const ev = {
      id: Date.now(),
      module: lastEvent.topic.split('.')[0],
      event_type: lastEvent.topic,
      timestamp: new Date().toISOString(),
      payload: JSON.stringify(lastEvent.payload),
      _live: true,
    };
    setLiveQueue(q => [ev, ...q].slice(0, 200));
  }, [lastEvent]);

  const allEvents = connected && liveQueue.length
    ? [...liveQueue, ...events]
    : events;

  const filtered = allEvents
    .filter(e => mod === 'ALL' || e.module === mod)
    .filter(e => !search || e.event_type.toLowerCase().includes(search.toLowerCase()) || (e.payload||'').toLowerCase().includes(search.toLowerCase()))
    .slice(0, 300);

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <div className="page-title">Log de <span>Eventos</span></div>
          <div className="page-subtitle">{filtered.length} eventos · {connected ? 'stream activo' : 'modo caché'}</div>
        </div>
        <div className="page-actions">
          <button className={`btn btn-sm ${autoScroll ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setAutoScroll(a=>!a)}>
            {autoScroll ? '⬇ AUTO' : '⬇ PAUSED'}
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => { setLiveQueue([]); refetch(); }}>↻ Limpiar</button>
        </div>
      </div>

      <div style={{ display:'flex', gap:10, marginBottom:12, flexWrap:'wrap', alignItems:'center' }}>
        <input className="search-input" placeholder="Buscar evento, payload..." value={search} onChange={e=>setSearch(e.target.value)} style={{ width:220 }} />
        <div className="filter-bar" style={{ margin:0 }}>
          {modules.map(m => <button key={m} className={`filter-tab ${mod===m?'active':''}`} onClick={()=>setMod(m)}>{m.toUpperCase()}</button>)}
        </div>
      </div>

      {/* Terminal-style feed */}
      <div className="card" style={{ padding:0 }}>
        <div style={{ background:'var(--bg-base)', padding:'8px 14px', borderBottom:'1px solid var(--border)', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <span style={{ fontFamily:'var(--font-mono)', fontSize:'0.68rem', color:'var(--text-muted)' }}>
            phantom@pi:~$ tail -f events.log
          </span>
          <div style={{ display:'flex', alignItems:'center', gap:6 }}>
            {connected && <div style={{ width:5, height:5, borderRadius:'50%', background:'var(--teal)', animation:'pulse-dot 2s infinite' }} />}
            <span style={{ fontSize:'0.62rem', color:'var(--text-muted)' }}>{connected ? 'LIVE' : 'OFFLINE'}</span>
          </div>
        </div>
        <div style={{ fontFamily:'var(--font-mono)', fontSize:'0.72rem', maxHeight:'calc(100vh - 280px)', overflowY:'auto', padding:'8px 0' }}>
          {filtered.length === 0 && (
            <div className="empty-state"><div className="empty-icon">≡</div><div className="empty-text">Sin eventos</div></div>
          )}
          {filtered.map((e, i) => (
            <div
              key={e.id || i}
              style={{
                display:'flex', gap:10, padding:'4px 14px',
                borderBottom:'1px solid var(--border)',
                background: e._live ? 'rgba(79,195,247,0.03)' : 'transparent',
                transition:'background 0.3s',
              }}
            >
              <span style={{ color:'var(--text-muted)', flexShrink:0, fontSize:'0.65rem', paddingTop:1 }}>{fmtTime(e.timestamp)}</span>
              <span style={{ color:'var(--blue-bright)', flexShrink:0, minWidth:72, fontSize:'0.68rem' }}>[{e.module}]</span>
              <span style={{ color: e.event_type.includes('error') ? 'var(--red)' : e.event_type.includes('detected') || e.event_type.includes('alert') ? 'var(--amber)' : 'var(--text-secondary)', flex:1, wordBreak:'break-all' }}>
                {e.event_type}
              </span>
              {e.payload && (
                <span style={{ color:'var(--text-muted)', fontSize:'0.65rem', maxWidth:200, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', flexShrink:0 }}>
                  {e.payload.slice(0,80)}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}