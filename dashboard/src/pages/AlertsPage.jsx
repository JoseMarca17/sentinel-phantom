// pages/AlertsPage.jsx
import { useState } from 'react';
import { useAlerts } from '../hooks/usePiData';
import { ackAlert } from '../services/api';
import { fmtRelative, fmtDate, fmtTime } from '../utils/time';

const SEV_ORDER = { CRITICAL:0, HIGH:1, MEDIUM:2, LOW:3, INFO:4 };
const SEV_COLOR = { CRITICAL:'var(--red)', HIGH:'var(--amber)', MEDIUM:'var(--blue-bright)', LOW:'var(--teal)', INFO:'var(--text-muted)' };

export default function AlertsPage() {
  const { data, refetch } = useAlerts();
  const [sev,    setSev]    = useState('ALL');
  const [mod,    setMod]    = useState('ALL');
  const [acked,  setAcked]  = useState('PENDING');
  const [search, setSearch] = useState('');

  const alerts = Array.isArray(data) ? data : [];

  const modules = ['ALL', ...new Set(alerts.map(a => a.module))];
  const sevs    = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];

  const filtered = alerts
    .filter(a => sev   === 'ALL' || a.severity === sev)
    .filter(a => mod   === 'ALL' || a.module   === mod)
    .filter(a => acked === 'ALL' || (acked === 'PENDING' ? !a.acknowledged : a.acknowledged))
    .filter(a => !search || a.description.toLowerCase().includes(search.toLowerCase()) || (a.device_mac||'').toLowerCase().includes(search.toLowerCase()))
    .sort((a,b) => SEV_ORDER[a.severity] - SEV_ORDER[b.severity] || new Date(b.timestamp) - new Date(a.timestamp));

  async function handleAck(id) {
    try { await ackAlert(id); } catch {}
    refetch();
  }

  const counts = { CRITICAL:0, HIGH:0, MEDIUM:0, LOW:0 };
  alerts.filter(a=>!a.acknowledged).forEach(a => { if(counts[a.severity]!==undefined) counts[a.severity]++; });

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <div className="page-title">Alertas de <span>Seguridad</span></div>
          <div className="page-subtitle">{filtered.length} alertas · {alerts.filter(a=>!a.acknowledged).length} pendientes</div>
        </div>
        <div className="page-actions">
          {['CRITICAL','HIGH','MEDIUM','LOW'].map(s => (
            counts[s] > 0 && (
              <div key={s} style={{ display:'flex', alignItems:'center', gap:4, fontSize:'0.68rem' }}>
                <div style={{ width:6, height:6, borderRadius:'50%', background: SEV_COLOR[s] }} />
                <span style={{ color: SEV_COLOR[s] }}>{counts[s]} {s}</span>
              </div>
            )
          ))}
          <button className="btn btn-ghost btn-sm" onClick={refetch}>↻ Actualizar</button>
        </div>
      </div>

      {/* Filtros */}
      <div style={{ display:'flex', gap:10, marginBottom:14, flexWrap:'wrap', alignItems:'center' }}>
        <input className="search-input" placeholder="Buscar MAC, descripción..." value={search} onChange={e=>setSearch(e.target.value)} style={{ width:220 }} />
        <div className="filter-bar" style={{ margin:0 }}>
          {sevs.map(s => <button key={s} className={`filter-tab ${sev===s?'active':''}`} onClick={()=>setSev(s)}>{s}</button>)}
        </div>
        <div className="filter-bar" style={{ margin:0 }}>
          {['ALL','PENDING','ACKED'].map(a => <button key={a} className={`filter-tab ${acked===a?'active':''}`} onClick={()=>setAcked(a)}>{a}</button>)}
        </div>
        <div className="filter-bar" style={{ margin:0 }}>
          {modules.map(m => <button key={m} className={`filter-tab ${mod===m?'active':''}`} onClick={()=>setMod(m)}>{m.toUpperCase()}</button>)}
        </div>
      </div>

      {/* Tabla */}
      <div className="card" style={{ padding:0 }}>
        <div className="table-wrap">
          <table className="tac-table">
            <thead>
              <tr>
                <th>Severidad</th><th>Módulo</th><th>Tipo</th>
                <th>Descripción</th><th>MAC</th><th>Tiempo</th><th>Estado</th><th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr><td colSpan={8}><div className="empty-state"><div className="empty-icon">✓</div><div className="empty-text">Sin alertas para los filtros seleccionados</div></div></td></tr>
              )}
              {filtered.map(a => (
                <tr key={a.id} style={{ opacity: a.acknowledged ? 0.5 : 1 }}>
                  <td>
                    <span className={`badge badge-${a.severity.toLowerCase()}`}>{a.severity}</span>
                  </td>
                  <td><span className="mono">{a.module}</span></td>
                  <td><span className="dim">{a.alert_type}</span></td>
                  <td style={{ maxWidth:260, color:'var(--text-primary)', fontSize:'0.75rem' }}>{a.description}</td>
                  <td><span className="mono">{a.device_mac || '—'}</span></td>
                  <td><span className="dim">{fmtRelative(a.timestamp)}</span></td>
                  <td>
                    {a.acknowledged
                      ? <span style={{ color:'var(--text-muted)', fontSize:'0.65rem' }}>ACK</span>
                      : <span style={{ color:'var(--red)', fontSize:'0.65rem' }}>PENDIENTE</span>}
                  </td>
                  <td>
                    {!a.acknowledged && (
                      <button className="btn btn-ghost btn-sm" onClick={() => handleAck(a.id)}>ACK</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}