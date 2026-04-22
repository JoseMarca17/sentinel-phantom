// pages/OverviewPage.jsx
import { useState, useEffect } from 'react';
import { useHealth, useAlerts, useEvents, useModules } from '../hooks/usePiData';
import { useSocket } from '../hooks/useSocket';
import { fmtRelative, fmtUptime } from '../utils/time';

const SEV_COLOR = { CRITICAL:'var(--red)', HIGH:'var(--amber)', MEDIUM:'var(--blue-bright)', LOW:'var(--teal)', INFO:'var(--text-muted)' };

function StatCard({ label, value, sub, color, accent }) {
  return (
    <div className="stat-card animate-in" style={{ '--accent-color': color }}>
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${accent || ''}`}>{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

function TermFeed({ events }) {
  return (
    <div className="terminal-feed">
      {events.slice(0,30).map((e, i) => (
        <div className="term-line" key={i}>
          <span className="term-ts">{new Date(e.timestamp).toLocaleTimeString('es-BO',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}</span>
          <span className="term-mod">[{e.module}]</span>
          <span className={`term-msg ${e.event_type.includes('error')?'err':e.event_type.includes('alert')||e.event_type.includes('detected')?'warn':''}`}>
            {e.event_type} {e.payload ? '→ '+e.payload.slice(0,60) : ''}
          </span>
        </div>
      ))}
      <div className="term-line"><span className="term-ts" /><span className="term-mod" /><span className="term-msg"><span className="term-cursor" /></span></div>
    </div>
  );
}

export default function OverviewPage() {
  const { data: health  } = useHealth();
  const { data: alerts  } = useAlerts();
  const { data: events  } = useEvents();
  const { data: modules } = useModules();
  const { connected, lastEvent } = useSocket();
  const [liveEvents, setLiveEvents] = useState([]);

  const alertsArr  = Array.isArray(alerts)  ? alerts  : [];
  const eventsArr  = Array.isArray(events)  ? events  : [];
  const modulesArr = Array.isArray(modules) ? modules : [];

  const critical = alertsArr.filter(a => a.severity === 'CRITICAL' && !a.acknowledged).length;
  const high     = alertsArr.filter(a => a.severity === 'HIGH'     && !a.acknowledged).length;
  const running  = modulesArr.filter(m => m.status === 'RUNNING').length;

  useEffect(() => {
    if (lastEvent) {
      setLiveEvents(prev => [{
        module: lastEvent.topic.split('.')[0],
        event_type: lastEvent.topic,
        timestamp: new Date().toISOString(),
        payload: JSON.stringify(lastEvent.payload).slice(0,80),
      }, ...prev].slice(0,50));
    }
  }, [lastEvent]);

  const feedEvents = connected && liveEvents.length ? liveEvents : eventsArr;

  return (
    <div className="animate-in">
      {/* Stats */}
      <div className="grid-4" style={{ marginBottom:16 }}>
        <StatCard label="Eventos totales"   value={health?.db_stats?.total_events  ?? 0} sub="últimas 24h"    color="var(--blue-core)"  accent="accent" />
        <StatCard label="Alertas activas"   value={health?.db_stats?.total_alerts  ?? 0} sub={`${critical} críticas`} color="var(--red)"  accent={critical > 0 ? 'red' : ''} />
        <StatCard label="Dispositivos"      value={health?.db_stats?.total_devices ?? 0} sub="detectados"     color="var(--blue-deep)"  accent="" />
        <StatCard label="Módulos activos"   value={running}                              sub={`de ${modulesArr.length} totales`} color="var(--teal)" accent="teal" />
      </div>

      <div className="grid-2-1" style={{ marginBottom:16 }}>
        {/* Terminal feed */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Feed <span className="card-title-accent">en vivo</span></span>
            <div style={{ display:'flex', alignItems:'center', gap:6, fontSize:'0.65rem', color: connected ? 'var(--teal)' : 'var(--text-muted)' }}>
              <div style={{ width:5, height:5, borderRadius:'50%', background: connected ? 'var(--teal)' : 'var(--text-muted)', animation: connected ? 'pulse-dot 2s infinite' : 'none' }} />
              {connected ? 'LIVE' : 'CACHED'}
            </div>
          </div>
          <TermFeed events={feedEvents} />
        </div>

        {/* Alertas recientes */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Alertas <span className="card-title-accent">recientes</span></span>
          </div>
          <div style={{ display:'flex', flexDirection:'column', gap:6, maxHeight:220, overflowY:'auto' }}>
            {alertsArr.slice(0,6).map(a => (
              <div key={a.id} className={`alert-item ${a.severity.toLowerCase()}`}>
                <div style={{ width:3, background: SEV_COLOR[a.severity]||'var(--text-muted)', borderRadius:2, alignSelf:'stretch' }} />
                <div className="alert-body">
                  <div className="alert-desc">{a.description.slice(0,60)}{a.description.length>60?'…':''}</div>
                  <div className="alert-meta">
                    <span>{a.module}</span>
                    <span>{fmtRelative(a.timestamp)}</span>
                    {!a.acknowledged && <span style={{ color:'var(--red)' }}>NO ACK</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Módulos */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Estado de <span className="card-title-accent">módulos</span></span>
        </div>
        <div className="grid-3">
          {modulesArr.map(m => (
            <div key={m.name} className={`module-card ${m.status.toLowerCase()}`}>
              <div className="module-card-top">
                <span className="module-name">{m.name.toUpperCase()}</span>
                <span className={`mod-chip ${m.status.toLowerCase()}`}>{m.status}</span>
              </div>
              <div className="module-stats">
                <div className="module-stat">
                  <span className="val">{fmtUptime(m.uptime)}</span>
                  <span className="lbl">Uptime</span>
                </div>
                <div className="module-stat">
                  <span className="val" style={{ color: m.error_count > 0 ? 'var(--red)' : 'var(--teal)' }}>{m.error_count}</span>
                  <span className="lbl">Errores</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}