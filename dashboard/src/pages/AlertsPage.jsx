import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { mockAlerts } from '../services/mockData';
import { formatDateTime } from '../utils/time';

export default function AlertsPage() {
  const { setPageTitle } = useOutletContext();
  const [alerts, setAlerts] = useState(mockAlerts);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    setPageTitle('ALERTAS');
  }, [setPageTitle]);

  const filtered = alerts.filter((a) => {
    if (filter === 'active') return !a.acked;
    if (filter === 'acked') return a.acked;
    return true;
  });

  const ack = (id) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, acked: true } : a)));
  };

  const ackAll = () => {
    setAlerts((prev) => prev.map((a) => ({ ...a, acked: true })));
  };

  const counts = {
    critical: alerts.filter((a) => a.level === 'critical' && !a.acked).length,
    warning: alerts.filter((a) => a.level === 'warning' && !a.acked).length,
    info: alerts.filter((a) => a.level === 'info' && !a.acked).length,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Summary metrics */}
      <div className="metric-grid">
        {[
          { label: 'CRÍTICAS', value: counts.critical, cls: 'red', metric: 'var(--accent-red)' },
          { label: 'ADVERTENCIAS', value: counts.warning, cls: 'amber', metric: 'var(--accent-amber)' },
          { label: 'INFO', value: counts.info, cls: 'accent', metric: 'var(--accent-primary)' },
          {
            label: 'RECONOCIDAS',
            value: alerts.filter((a) => a.acked).length,
            cls: '',
            metric: 'var(--text-muted)',
          },
        ].map((m) => (
          <div className="metric-card" key={m.label} style={{ '--metric-color': m.metric }}>
            <div className="metric-label">{m.label}</div>
            <div className={`metric-value ${m.cls}`}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">REGISTRO DE ALERTAS</span>
          <div style={{ display: 'flex', gap: 8 }}>
            <FilterButtons filter={filter} setFilter={setFilter} />
            <button className="btn btn-ghost btn-sm" onClick={ackAll}>
              RECONOCER TODO
            </button>
          </div>
        </div>
        <div>
          {filtered.length === 0 ? (
            <div className="empty-state">// Sin alertas en este filtro</div>
          ) : (
            <table className="data-table" style={{ width: '100%' }}>
              <thead>
                <tr>
                  <th>NIVEL</th>
                  <th>MÓDULO</th>
                  <th>MENSAJE</th>
                  <th>TIMESTAMP</th>
                  <th>ACCIÓN</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((alert) => (
                  <tr key={alert.id} style={{ opacity: alert.acked ? 0.5 : 1 }}>
                    <td>
                      <span className={`badge ${alert.level}`}>
                        <span className="badge-dot" />
                        {alert.level}
                      </span>
                    </td>
                    <td>
                      <span
                        className="chip"
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: 11,
                          textTransform: 'uppercase',
                        }}
                      >
                        {alert.module}
                      </span>
                    </td>
                    <td style={{ maxWidth: 380, color: 'var(--text-primary)', fontSize: 13 }}>
                      {alert.message}
                    </td>
                    <td className="mono" style={{ whiteSpace: 'nowrap', fontSize: 11 }}>
                      {formatDateTime(alert.timestamp)}
                    </td>
                    <td>
                      {!alert.acked ? (
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={() => ack(alert.id)}
                        >
                          ACK
                        </button>
                      ) : (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
                          ✓ acked
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

function FilterButtons({ filter, setFilter }) {
  const options = [
    { value: 'all', label: 'TODOS' },
    { value: 'active', label: 'ACTIVOS' },
    { value: 'acked', label: 'RECONOCIDOS' },
  ];
  return (
    <div style={{ display: 'flex', gap: 4 }}>
      {options.map((opt) => (
        <button
          key={opt.value}
          className={`btn btn-sm ${filter === opt.value ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setFilter(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
