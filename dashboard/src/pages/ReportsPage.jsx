// pages/ReportsPage.jsx
import { useState } from 'react';
import { fmtRelative } from '../utils/time';
import { mockAlerts, mockDevices, mockSession, mockStats } from '../services/mockData';

export default function ReportsPage() {
  const alerts  = mockAlerts;
  const devices = mockDevices;
  const session = mockSession;

  const critical = alerts.filter(a => a.severity === 'CRITICAL').length;
  const high     = alerts.filter(a => a.severity === 'HIGH').length;
  const byModule = {};
  alerts.forEach(a => { byModule[a.module] = (byModule[a.module]||0)+1; });

  const byType = {};
  devices.forEach(d => { byType[d.device_type] = (byType[d.device_type]||0)+1; });

  function exportJSON() {
    const data = { session, alerts, devices, generated_at: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(data,null,2)], { type:'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `phantom_report_${session.id.slice(0,8)}.json`;
    a.click();
  }

  function exportCSV() {
    const rows = [
      ['id','module','severity','description','timestamp','device_mac'],
      ...alerts.map(a => [a.id, a.module, a.severity, `"${a.description}"`, a.timestamp, a.device_mac||''])
    ];
    const csv = rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type:'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'phantom_alerts.csv';
    a.click();
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <div className="page-title">Reportes <span>Forenses</span></div>
          <div className="page-subtitle">Sesión {session.id.slice(0,8).toUpperCase()} · {fmtRelative(session.started_at)}</div>
        </div>
        <div className="page-actions">
          <button className="btn btn-ghost btn-sm" onClick={exportCSV}>↓ Exportar CSV</button>
          <button className="btn btn-primary btn-sm" onClick={exportJSON}>↓ Exportar JSON</button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom:16 }}>
        {[
          { label:'Total alertas', value:alerts.length,  color:'var(--blue-core)' },
          { label:'Críticas',      value:critical,        color:'var(--red)' },
          { label:'Altas',         value:high,            color:'var(--amber)' },
          { label:'Dispositivos',  value:devices.length,  color:'var(--teal)' },
        ].map(s => (
          <div key={s.label} className="stat-card" style={{ '--accent-color': s.color }}>
            <div className="stat-label">{s.label}</div>
            <div className="stat-value">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom:16 }}>
        {/* Alertas por módulo */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Alertas por <span className="card-title-accent">módulo</span></span>
          </div>
          <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
            {Object.entries(byModule).sort((a,b)=>b[1]-a[1]).map(([mod,n]) => (
              <div key={mod} style={{ display:'flex', alignItems:'center', gap:10 }}>
                <span style={{ fontSize:'0.72rem', color:'var(--text-secondary)', minWidth:80, fontFamily:'var(--font-mono)' }}>{mod}</span>
                <div style={{ flex:1, height:6, background:'var(--bg-elevated)', borderRadius:3, overflow:'hidden' }}>
                  <div style={{ height:'100%', width:`${(n/alerts.length)*100}%`, background:'var(--blue-core)', borderRadius:3, transition:'width 0.5s ease' }} />
                </div>
                <span style={{ fontSize:'0.72rem', color:'var(--blue-bright)', minWidth:20, textAlign:'right' }}>{n}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Info de sesión */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Info de <span className="card-title-accent">sesión</span></span>
          </div>
          <div style={{ display:'flex', flexDirection:'column' }}>
            {[
              ['Session ID',  session.id.slice(0,20)+'...'],
              ['Device',      session.device_id],
              ['Inicio',      fmtRelative(session.started_at)],
              ['Estado',      session.ended_at ? 'Cerrada' : 'Activa'],
              ['Notas',       session.notes],
            ].map(([k,v]) => (
              <div key={k} style={{ display:'flex', justifyContent:'space-between', padding:'8px 0', borderBottom:'1px solid var(--border)', fontSize:'0.73rem' }}>
                <span style={{ color:'var(--text-muted)' }}>{k}</span>
                <span style={{ color:'var(--text-secondary)', fontFamily:'var(--font-mono)', fontSize:'0.68rem', maxWidth:180, textAlign:'right', wordBreak:'break-all' }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Dispositivos por tipo */}
      <div className="card" style={{ marginBottom:16 }}>
        <div className="card-header">
          <span className="card-title">Dispositivos por <span className="card-title-accent">tipo</span></span>
        </div>
        <div className="grid-3">
          {Object.entries(byType).map(([type, n]) => (
            <div key={type} style={{ background:'var(--bg-elevated)', border:'1px solid var(--border)', borderRadius:'var(--r-md)', padding:'12px 14px' }}>
              <div style={{ fontFamily:'var(--font-display)', fontSize:'1.4rem', fontWeight:700, color:'var(--blue-bright)' }}>{n}</div>
              <div style={{ fontSize:'0.65rem', color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.1em', marginTop:4 }}>{type}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Timeline de alertas críticas */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Timeline <span className="card-title-accent">crítico</span></span>
        </div>
        <div style={{ display:'flex', flexDirection:'column', gap:0 }}>
          {alerts.filter(a => ['CRITICAL','HIGH'].includes(a.severity)).map((a,i) => (
            <div key={a.id} style={{ display:'flex', gap:14, padding:'10px 0', borderBottom:'1px solid var(--border)' }}>
              <div style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:0 }}>
                <div style={{ width:10, height:10, borderRadius:'50%', background: a.severity==='CRITICAL' ? 'var(--red)' : 'var(--amber)', flexShrink:0, marginTop:4 }} />
                {i < alerts.filter(a=>['CRITICAL','HIGH'].includes(a.severity)).length-1 && (
                  <div style={{ width:1, flex:1, background:'var(--border)', minHeight:20, marginTop:2 }} />
                )}
              </div>
              <div style={{ flex:1, paddingBottom:4 }}>
                <div style={{ fontSize:'0.75rem', color:'var(--text-primary)', marginBottom:3 }}>{a.description}</div>
                <div style={{ display:'flex', gap:10, fontSize:'0.65rem', color:'var(--text-muted)' }}>
                  <span style={{ color: a.severity==='CRITICAL' ? 'var(--red)' : 'var(--amber)' }}>{a.severity}</span>
                  <span>{a.module}</span>
                  <span>{fmtRelative(a.timestamp)}</span>
                  {a.device_mac && <span style={{ fontFamily:'var(--font-mono)', color:'var(--blue-bright)' }}>{a.device_mac}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}