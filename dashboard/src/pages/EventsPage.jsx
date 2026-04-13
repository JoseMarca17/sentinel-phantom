import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { mockEvents } from '../services/mockData';
import { formatDateTime } from '../utils/time';

const MODULE_COLORS = {
  wifi: 'var(--accent-primary)',
  bluetooth: 'var(--accent-purple)',
  rfid: 'var(--accent-green)',
  tscm: 'var(--accent-amber)',
  ir: 'var(--accent-red)',
  nrf24: 'var(--accent-green)',
};

export default function EventsPage() {
  const { setPageTitle } = useOutletContext();
  const [events] = useState(mockEvents);
  const [moduleFilter, setModuleFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    setPageTitle('EVENTOS');
  }, [setPageTitle]);

  const modules = ['all', ...new Set(events.map((e) => e.module))];
  const severities = ['all', 'critical', 'high', 'medium', 'low'];

  const filtered = events.filter((ev) => {
    if (moduleFilter !== 'all' && ev.module !== moduleFilter) return false;
    if (severityFilter !== 'all' && ev.severity !== severityFilter) return false;
    if (search && !JSON.stringify(ev).toLowerCase().includes(search.toLowerCase()))
      return false;
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Filters */}
      <div className="card">
        <div className="card-body" style={{ paddingTop: 12, paddingBottom: 12 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: 1 }}>
              MÓDULO:
            </span>
            {modules.map((m) => (
              <button
                key={m}
                className={`btn btn-sm ${moduleFilter === m ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setModuleFilter(m)}
                style={{ textTransform: 'uppercase' }}
              >
                {m}
              </button>
            ))}
            <div style={{ flex: 1, minWidth: 20 }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: 1 }}>
              SEVERIDAD:
            </span>
            {severities.map((s) => (
              <button
                key={s}
                className={`btn btn-sm ${severityFilter === s ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setSeverityFilter(s)}
                style={{ textTransform: 'uppercase' }}
              >
                {s}
              </button>
            ))}
          </div>
          <div style={{ marginTop: 10 }}>
            <input
              type="text"
              placeholder="Buscar en eventos..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: '100%',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-base)',
                borderRadius: 4,
                padding: '7px 12px',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                outline: 'none',
              }}
            />
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        {/* Events list */}
        <div className="card" style={{ flex: 1 }}>
          <div className="card-header">
            <span className="card-title">EVENTOS ({filtered.length})</span>
          </div>
          <div>
            {filtered.length === 0 ? (
              <div className="empty-state">// Sin resultados</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>TIPO</th>
                    <th>MÓDULO</th>
                    <th>SEVERIDAD</th>
                    <th>TIMESTAMP</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((ev) => (
                    <tr
                      key={ev.id}
                      onClick={() => setSelected(ev)}
                      style={{
                        cursor: 'pointer',
                        background:
                          selected?.id === ev.id ? 'var(--accent-primary-dim)' : undefined,
                      }}
                    >
                      <td className="mono" style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                        {ev.id}
                      </td>
                      <td>
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: 12,
                            color: MODULE_COLORS[ev.module] || 'var(--text-secondary)',
                          }}
                        >
                          {ev.type}
                        </span>
                      </td>
                      <td>
                        <span className="chip" style={{ textTransform: 'uppercase', fontSize: 10 }}>
                          {ev.module}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${ev.severity}`}>
                          <span className="badge-dot" />
                          {ev.severity}
                        </span>
                      </td>
                      <td className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {formatDateTime(ev.timestamp)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Event detail panel */}
        {selected && (
          <div className="card" style={{ width: 320, alignSelf: 'flex-start' }}>
            <div className="card-header">
              <span className="card-title">DETALLE</span>
              <button
                className="btn btn-ghost btn-sm btn-icon"
                onClick={() => setSelected(null)}
                style={{ fontSize: 14, padding: '4px 8px' }}
              >
                ✕
              </button>
            </div>
            <div className="card-body">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <DetailRow label="ID" value={`EVT-${selected.id}`} mono />
                <DetailRow label="TIPO" value={selected.type} mono accent />
                <DetailRow label="MÓDULO" value={selected.module.toUpperCase()} />
                <DetailRow label="SEVERIDAD">
                  <span className={`badge ${selected.severity}`}>
                    <span className="badge-dot" />
                    {selected.severity}
                  </span>
                </DetailRow>
                <DetailRow label="TIMESTAMP" value={formatDateTime(selected.timestamp)} mono />
                <div>
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 10,
                      color: 'var(--text-muted)',
                      marginBottom: 6,
                      letterSpacing: 1,
                    }}
                  >
                    DATA PAYLOAD
                  </div>
                  <pre
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11,
                      color: 'var(--accent-green)',
                      background: 'var(--bg-input)',
                      border: '1px solid var(--border-base)',
                      borderRadius: 4,
                      padding: 10,
                      overflow: 'auto',
                      margin: 0,
                      maxHeight: 200,
                    }}
                  >
                    {JSON.stringify(selected.data, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function DetailRow({ label, value, mono, accent, children }) {
  return (
    <div>
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 9,
          color: 'var(--text-muted)',
          letterSpacing: 1.5,
          marginBottom: 3,
        }}
      >
        {label}
      </div>
      {children || (
        <div
          style={{
            fontFamily: mono ? 'var(--font-mono)' : 'var(--font-body)',
            fontSize: 13,
            color: accent ? 'var(--accent-primary)' : 'var(--text-primary)',
          }}
        >
          {value}
        </div>
      )}
    </div>
  );
}
