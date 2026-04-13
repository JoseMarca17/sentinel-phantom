import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { mockDevices } from '../services/mockData';
import { formatDateTime } from '../utils/time';

const TYPE_COLOR = {
  wifi: 'var(--accent-primary)',
  bluetooth: 'var(--accent-purple)',
  rfid: 'var(--accent-green)',
};

const THREAT_BADGE = {
  critical: 'critical',
  high: 'high',
  medium: 'warning',
  low: 'low',
  none: 'success',
};

export default function DevicesPage() {
  const { setPageTitle } = useOutletContext();
  const [devices, setDevices] = useState(mockDevices);
  const [typeFilter, setTypeFilter] = useState('all');
  const [trustFilter, setTrustFilter] = useState('all');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    setPageTitle('DISPOSITIVOS');
  }, [setPageTitle]);

  const types = ['all', 'wifi', 'bluetooth', 'rfid'];

  const filtered = devices.filter((d) => {
    if (typeFilter !== 'all' && d.type !== typeFilter) return false;
    if (trustFilter === 'trusted' && !d.trusted) return false;
    if (trustFilter === 'untrusted' && d.trusted) return false;
    if (trustFilter === 'threats' && d.threat_level === 'none') return false;
    return true;
  });

  const toggleTrust = (id) => {
    setDevices((prev) =>
      prev.map((d) => (d.id === id ? { ...d, trusted: !d.trusted } : d))
    );
    if (selected?.id === id) {
      setSelected((s) => ({ ...s, trusted: !s.trusted }));
    }
  };

  const counts = {
    total: devices.length,
    trusted: devices.filter((d) => d.trusted).length,
    threats: devices.filter((d) => d.threat_level !== 'none').length,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Metrics */}
      <div className="metric-grid">
        <div className="metric-card" style={{ '--metric-color': 'var(--accent-primary)' }}>
          <div className="metric-label">TOTAL DISPOSITIVOS</div>
          <div className="metric-value accent">{counts.total}</div>
        </div>
        <div className="metric-card" style={{ '--metric-color': 'var(--accent-green)' }}>
          <div className="metric-label">EN WHITELIST</div>
          <div className="metric-value green">{counts.trusted}</div>
        </div>
        <div className="metric-card" style={{ '--metric-color': 'var(--accent-red)' }}>
          <div className="metric-label">CON AMENAZA</div>
          <div className="metric-value red">{counts.threats}</div>
        </div>
        <div className="metric-card" style={{ '--metric-color': 'var(--accent-amber)' }}>
          <div className="metric-label">NO AUTORIZADOS</div>
          <div className="metric-value amber">{devices.filter((d) => !d.trusted).length}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="card-body" style={{ paddingTop: 12, paddingBottom: 12 }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: 1 }}>
              TIPO:
            </span>
            {types.map((t) => (
              <button
                key={t}
                className={`btn btn-sm ${typeFilter === t ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setTypeFilter(t)}
                style={{ textTransform: 'uppercase' }}
              >
                {t}
              </button>
            ))}
            <div style={{ width: 20 }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: 1 }}>
              ESTADO:
            </span>
            {[
              { val: 'all', label: 'TODOS' },
              { val: 'trusted', label: 'AUTORIZADOS' },
              { val: 'untrusted', label: 'NO AUTORIZADOS' },
              { val: 'threats', label: 'AMENAZAS' },
            ].map((opt) => (
              <button
                key={opt.val}
                className={`btn btn-sm ${trustFilter === opt.val ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setTrustFilter(opt.val)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        {/* Device table */}
        <div className="card" style={{ flex: 1 }}>
          <div className="card-header">
            <span className="card-title">DISPOSITIVOS DETECTADOS ({filtered.length})</span>
          </div>
          <div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>MAC / UID</th>
                  <th>TIPO</th>
                  <th>FABRICANTE</th>
                  <th>IDENTIFICADOR</th>
                  <th>AMENAZA</th>
                  <th>CONFIANZA</th>
                  <th>ACCIÓN</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((dev) => (
                  <tr
                    key={dev.id}
                    onClick={() => setSelected(dev)}
                    style={{
                      cursor: 'pointer',
                      background:
                        selected?.id === dev.id ? 'var(--accent-primary-dim)' : undefined,
                    }}
                  >
                    <td className="mono" style={{ fontSize: 12 }}>
                      {dev.mac}
                    </td>
                    <td>
                      <span
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: 11,
                          color: TYPE_COLOR[dev.type] || 'var(--text-muted)',
                          textTransform: 'uppercase',
                        }}
                      >
                        {dev.type}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{dev.vendor}</td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                      {dev.ssid || dev.name || <span style={{ color: 'var(--text-muted)' }}>—</span>}
                    </td>
                    <td>
                      <span className={`badge ${THREAT_BADGE[dev.threat_level]}`}>
                        <span className="badge-dot" />
                        {dev.threat_level}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${dev.trusted ? 'success' : 'offline'}`}>
                        {dev.trusted ? '✓ autorizado' : '✕ no autorizado'}
                      </span>
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <button
                        className={`btn btn-sm ${dev.trusted ? 'btn-danger' : 'btn-success'}`}
                        onClick={() => toggleTrust(dev.id)}
                      >
                        {dev.trusted ? 'REVOCAR' : 'AUTORIZAR'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Detail side panel */}
        {selected && (
          <div className="card" style={{ width: 300, alignSelf: 'flex-start', flexShrink: 0 }}>
            <div className="card-header">
              <span className="card-title">DETALLE</span>
              <button
                className="btn btn-ghost btn-sm btn-icon"
                onClick={() => setSelected(null)}
                style={{ padding: '4px 8px' }}
              >
                ✕
              </button>
            </div>
            <div className="card-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <FieldRow label="MAC / UID" value={selected.mac} mono />
                <FieldRow label="TIPO" value={selected.type.toUpperCase()} mono />
                <FieldRow label="FABRICANTE" value={selected.vendor} />
                <FieldRow label="NOMBRE / SSID" value={selected.ssid || selected.name || '—'} />
                <FieldRow label="PRIMERA VEZ VISTO" value={formatDateTime(selected.first_seen)} mono small />
                <FieldRow label="ÚLTIMA VEZ VISTO" value={formatDateTime(selected.last_seen)} mono small />
                <FieldRow label="NIVEL DE AMENAZA">
                  <span className={`badge ${THREAT_BADGE[selected.threat_level]}`}>
                    <span className="badge-dot" />
                    {selected.threat_level}
                  </span>
                </FieldRow>
                <FieldRow label="CONFIANZA">
                  <span className={`badge ${selected.trusted ? 'success' : 'offline'}`}>
                    {selected.trusted ? '✓ autorizado' : '✕ no autorizado'}
                  </span>
                </FieldRow>
                <button
                  className={`btn ${selected.trusted ? 'btn-danger' : 'btn-success'}`}
                  onClick={() => toggleTrust(selected.id)}
                  style={{ width: '100%', justifyContent: 'center', marginTop: 4 }}
                >
                  {selected.trusted ? '✕ REVOCAR AUTORIZACIÓN' : '✓ AUTORIZAR DISPOSITIVO'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function FieldRow({ label, value, mono, small, children }) {
  return (
    <div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', letterSpacing: 1.5, marginBottom: 3 }}>
        {label}
      </div>
      {children || (
        <div style={{
          fontFamily: mono ? 'var(--font-mono)' : 'var(--font-body)',
          fontSize: small ? 11 : 13,
          color: 'var(--text-primary)',
        }}>
          {value}
        </div>
      )}
    </div>
  );
}
