// pages/DevicesPage.jsx
import { useState } from 'react';
import { useDevices } from '../hooks/usePiData';
import { fmtRelative } from '../utils/time';

const THREAT_COLOR = { CRITICAL:'var(--red)', HIGH:'var(--amber)', MEDIUM:'var(--blue-bright)', LOW:'var(--teal)', INFO:'var(--text-muted)' };
const TYPE_ICON    = { wifi:'📡', bluetooth:'◉', rfid:'◈', drone:'△', ir:'◎', tscm:'◆' };

export default function DevicesPage() {
  const { data, refetch } = useDevices();
  const [type,   setType]   = useState('ALL');
  const [threat, setThreat] = useState('ALL');
  const [search, setSearch] = useState('');

  const devices = Array.isArray(data) ? data : [];
  const types   = ['ALL', ...new Set(devices.map(d => d.device_type))];
  const threats = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];

  const filtered = devices
    .filter(d => type   === 'ALL' || d.device_type  === type)
    .filter(d => threat === 'ALL' || d.threat_level === threat)
    .filter(d => !search || (d.mac||'').toLowerCase().includes(search.toLowerCase()) || (d.vendor||'').toLowerCase().includes(search.toLowerCase()) || (d.ssid||'').toLowerCase().includes(search.toLowerCase()))
    .sort((a,b) => {
      const order = { CRITICAL:0, HIGH:1, MEDIUM:2, LOW:3, INFO:4 };
      return (order[a.threat_level]??5) - (order[b.threat_level]??5);
    });

  const byType = {};
  devices.forEach(d => { byType[d.device_type] = (byType[d.device_type]||0)+1; });

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <div className="page-title">Dispositivos <span>Detectados</span></div>
          <div className="page-subtitle">{filtered.length} de {devices.length} dispositivos</div>
        </div>
        <div className="page-actions">
          {Object.entries(byType).map(([t,n]) => (
            <div key={t} style={{ fontSize:'0.68rem', color:'var(--text-secondary)' }}>
              {TYPE_ICON[t]||'◦'} {t}: <span style={{ color:'var(--blue-bright)' }}>{n}</span>
            </div>
          ))}
          <button className="btn btn-ghost btn-sm" onClick={refetch}>↻</button>
        </div>
      </div>

      {/* Filtros */}
      <div style={{ display:'flex', gap:10, marginBottom:14, flexWrap:'wrap', alignItems:'center' }}>
        <input className="search-input" placeholder="MAC, vendor, SSID..." value={search} onChange={e=>setSearch(e.target.value)} style={{ width:200 }} />
        <div className="filter-bar" style={{ margin:0 }}>
          {types.map(t => <button key={t} className={`filter-tab ${type===t?'active':''}`} onClick={()=>setType(t)}>{t.toUpperCase()}</button>)}
        </div>
        <div className="filter-bar" style={{ margin:0 }}>
          {threats.map(t => <button key={t} className={`filter-tab ${threat===t?'active':''}`} onClick={()=>setThreat(t)}>{t}</button>)}
        </div>
      </div>

      <div className="card" style={{ padding:0 }}>
        <div className="table-wrap">
          <table className="tac-table">
            <thead>
              <tr><th>Tipo</th><th>MAC</th><th>Vendor</th><th>SSID / Info</th><th>Señal</th><th>Amenaza</th><th>Visto</th></tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr><td colSpan={7}><div className="empty-state"><div className="empty-icon">◎</div><div className="empty-text">Sin dispositivos para los filtros</div></div></td></tr>
              )}
              {filtered.map(d => (
                <tr key={d.id}>
                  <td>
                    <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                      <span style={{ fontSize:'1rem' }}>{TYPE_ICON[d.device_type]||'◦'}</span>
                      <span className="dim">{d.device_type}</span>
                    </div>
                  </td>
                  <td><span className="mono">{d.mac || '—'}</span></td>
                  <td style={{ color:'var(--text-secondary)', fontSize:'0.73rem' }}>{d.vendor || '—'}</td>
                  <td><span className="dim">{d.ssid || '—'}</span></td>
                  <td>
                    {d.signal_dbm != null && (
                      <span style={{ color: d.signal_dbm > -60 ? 'var(--red)' : d.signal_dbm > -75 ? 'var(--amber)' : 'var(--text-muted)', fontSize:'0.72rem' }}>
                        {d.signal_dbm} dBm
                      </span>
                    )}
                    {d.signal_dbm == null && <span className="dim">—</span>}
                  </td>
                  <td>
                    <span className={`badge badge-${(d.threat_level||'info').toLowerCase()}`}>{d.threat_level}</span>
                  </td>
                  <td><span className="dim">{fmtRelative(d.last_seen)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}