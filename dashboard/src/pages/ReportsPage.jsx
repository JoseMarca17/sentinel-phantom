import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { mockAlerts, mockEvents, mockDevices, mockSystemStatus, mockModules } from '../services/mockData';
import { formatDateTime } from '../utils/time';

export default function ReportsPage() {
  const { setPageTitle } = useOutletContext();
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    setPageTitle('REPORTES');
  }, [setPageTitle]);

  const handleExport = () => {
    setExporting(true);
    // Build CSV from mock data
    const rows = [
      ['ID', 'TIPO', 'MÓDULO', 'SEVERIDAD', 'TIMESTAMP'],
      ...mockEvents.map((e) => [
        e.id,
        e.type,
        e.module,
        e.severity,
        formatDateTime(e.timestamp),
      ]),
    ];
    const csv = rows.map((r) => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sentinel-phantom-${mockSystemStatus.session_id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    setTimeout(() => setExporting(false), 1000);
  };

  const threatsByModule = mockModules.map((m) => ({
    ...m,
    alerts: mockAlerts.filter((a) => a.module === m.name).length,
    critical: mockAlerts.filter((a) => a.module === m.name && a.level === 'critical').length,
  }));

  const topThreats = mockAlerts
    .filter((a) => a.level === 'critical' || a.level === 'warning')
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 5);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Session header */}
      <div className="card" style={{ borderLeft: '3px solid var(--accent-primary)' }}>
        <div className="card-body">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', letterSpacing: 2, marginBottom: 6 }}>
                REPORTE DE SESIÓN
              </div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, color: 'var(--accent-primary)', letterSpacing: 2 }}>
                {mockSystemStatus.session_id}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                Inicio: {formatDateTime(mockSystemStatus.session_start)} · Duración: {mockSystemStatus.uptime}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn btn-primary"
                onClick={handleExport}
                disabled={exporting}
              >
                {exporting ? '↓ exportando...' : '↓ EXPORTAR CSV'}
              </button>
              <button className="btn btn-ghost" onClick={() => window.print()}>
                ⎙ IMPRIMIR
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Summary metrics */}
      <div className="metric-grid">
        {[
          { label: 'TOTAL EVENTOS', value: mockEvents.length, color: 'accent', metric: 'var(--accent-primary)' },
          { label: 'ALERTAS CRÍTICAS', value: mockAlerts.filter((a) => a.level === 'critical').length, color: 'red', metric: 'var(--accent-red)' },
          { label: 'DISPOSITIVOS DETECTADOS', value: mockDevices.length, color: 'amber', metric: 'var(--accent-amber)' },
          { label: 'MÓDULOS ACTIVOS', value: mockModules.filter((m) => m.status === 'active').length, color: 'green', metric: 'var(--accent-green)' },
        ].map((m) => (
          <div className="metric-card" key={m.label} style={{ '--metric-color': m.metric }}>
            <div className="metric-label">{m.label}</div>
            <div className={`metric-value ${m.color}`}>{m.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Events by module */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">ACTIVIDAD POR MÓDULO</span>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {threatsByModule.map((mod) => {
              const maxEvents = Math.max(...threatsByModule.map((m) => m.events_count), 1);
              return (
                <div key={mod.name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                      {mod.label}
                    </span>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      {mod.critical > 0 && (
                        <span className="badge critical" style={{ padding: '1px 6px' }}>
                          {mod.critical} críticas
                        </span>
                      )}
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                        {mod.events_count} eventos
                      </span>
                    </div>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${(mod.events_count / maxEvents) * 100}%`,
                        background: mod.critical > 0 ? 'var(--accent-red)' : 'var(--accent-primary)',
                        opacity: 0.7,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top threats */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">PRINCIPALES AMENAZAS</span>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {topThreats.map((alert, i) => (
              <div
                key={alert.id}
                style={{
                  display: 'flex',
                  gap: 12,
                  paddingBottom: 12,
                  marginBottom: 12,
                  borderBottom: i < topThreats.length - 1 ? '1px solid var(--border-card)' : 'none',
                  alignItems: 'flex-start',
                }}
              >
                <div style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                  color: 'var(--text-muted)',
                  paddingTop: 2,
                  minWidth: 16,
                }}>
                  {i + 1}.
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', marginBottom: 4, lineHeight: 1.4 }}>
                    {alert.message}
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span className={`badge ${alert.level}`}>
                      <span className="badge-dot" />
                      {alert.level}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      {alert.module}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Full event log */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">LOG COMPLETO DE EVENTOS</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
            {mockEvents.length} registros
          </span>
        </div>
        <div>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>TIPO</th>
                <th>MÓDULO</th>
                <th>SEVERIDAD</th>
                <th>DATOS CLAVE</th>
                <th>TIMESTAMP</th>
              </tr>
            </thead>
            <tbody>
              {mockEvents.map((ev) => (
                <tr key={ev.id}>
                  <td className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>{ev.id}</td>
                  <td className="mono" style={{ fontSize: 12, color: 'var(--accent-primary)' }}>{ev.type}</td>
                  <td>
                    <span className="chip" style={{ textTransform: 'uppercase', fontSize: 10 }}>{ev.module}</span>
                  </td>
                  <td>
                    <span className={`badge ${ev.severity}`}>
                      <span className="badge-dot" />{ev.severity}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)', maxWidth: 300 }}>
                    {Object.entries(ev.data).slice(0, 2).map(([k, v]) => `${k}:${v}`).join(' | ')}
                  </td>
                  <td className="mono" style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {formatDateTime(ev.timestamp)}
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
