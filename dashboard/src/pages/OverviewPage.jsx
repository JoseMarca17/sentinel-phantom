import { useState, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
  mockSystemStatus,
  mockModules,
  mockAlerts,
  mockTimelineData,
} from '../services/mockData';
import { formatDistanceToNow } from '../utils/time';

export default function OverviewPage() {
  const { setPageTitle } = useOutletContext();
  const navigate = useNavigate();
  const [alerts] = useState(mockAlerts.filter((a) => !a.acked));

  useEffect(() => {
    setPageTitle('OVERVIEW');
  }, [setPageTitle]);

  const totalEvents = mockModules.reduce((s, m) => s + m.events_count, 0);
  const activeModules = mockModules.filter((m) => m.status === 'active').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Top metric row */}
      <div className="metric-grid">
        <div className="metric-card" style={{ '--metric-color': 'var(--accent-red)' }}>
          <div className="metric-label">ALERTAS ACTIVAS</div>
          <div className="metric-value red">{alerts.length}</div>
          <div className="metric-sub">sin reconocer</div>
        </div>
        <div className="metric-card" style={{ '--metric-color': 'var(--accent-amber)' }}>
          <div className="metric-label">EVENTOS HOY</div>
          <div className="metric-value amber">{totalEvents}</div>
          <div className="metric-sub">en sesión activa</div>
        </div>
        <div className="metric-card" style={{ '--metric-color': 'var(--accent-green)' }}>
          <div className="metric-label">MÓDULOS ACTIVOS</div>
          <div className="metric-value green">{activeModules}</div>
          <div className="metric-sub">de {mockModules.length} total</div>
        </div>
        <div className="metric-card" style={{ '--metric-color': 'var(--accent-primary)' }}>
          <div className="metric-label">UPTIME SESIÓN</div>
          <div className="metric-value accent">{mockSystemStatus.uptime}</div>
          <div className="metric-sub">desde arranque</div>
        </div>
      </div>

      <div className="grid-2">
        {/* Modules status */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">ESTADO DE MÓDULOS</span>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/modules/wifi')}>
              VER TODO
            </button>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            {mockModules.map((mod) => (
              <ModuleRow key={mod.name} module={mod} navigate={navigate} />
            ))}
          </div>
        </div>

        {/* Active alerts */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">ALERTAS RECIENTES</span>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/alerts')}>
              VER TODO
            </button>
          </div>
          <div className="card-body">
            {alerts.length === 0 ? (
              <div className="empty-state">// Sin alertas activas</div>
            ) : (
              alerts.slice(0, 4).map((alert) => (
                <AlertRow key={alert.id} alert={alert} />
              ))
            )}
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Timeline mini chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">ACTIVIDAD — ÚLTIMA HORA</span>
          </div>
          <div className="card-body">
            <TimelineChart data={mockTimelineData} />
          </div>
        </div>

        {/* System health */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">SALUD DEL SISTEMA</span>
          </div>
          <div className="card-body">
            <SystemHealth status={mockSystemStatus} />
          </div>
        </div>
      </div>
    </div>
  );
}

function ModuleRow({ module, navigate }) {
  const statusColor = {
    active: 'var(--accent-green)',
    scanning: 'var(--accent-primary)',
    idle: 'var(--text-muted)',
  }[module.status] || 'var(--text-muted)';

  return (
    <div
      className="data-table"
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '10px 18px',
        borderBottom: '1px solid var(--border-card)',
        cursor: 'pointer',
        gap: 12,
      }}
      onClick={() => navigate(`/modules/${module.name}`)}
    >
      <span style={{ color: statusColor, fontSize: 8 }}>●</span>
      <span
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 13,
          fontWeight: 600,
          flex: 1,
          color: 'var(--text-primary)',
        }}
      >
        {module.label}
      </span>
      <span className="badge" style={{ textTransform: 'none' }}>
        {module.events_count} eventos
      </span>
      <span className={`badge ${module.status}`}>
        <span className="badge-dot" />
        {module.status}
      </span>
    </div>
  );
}

function AlertRow({ alert }) {
  const icons = {
    critical: '⚠',
    warning: '◈',
    info: '◉',
  };
  return (
    <div className={`alert-item ${alert.level}`}>
      <div className="alert-icon-wrap">
        <span style={{ fontSize: 14 }}>{icons[alert.level]}</span>
      </div>
      <div style={{ flex: 1 }}>
        <div className="alert-message">{alert.message}</div>
        <div className="alert-meta">
          <span className={`badge ${alert.level}`}>
            <span className="badge-dot" />
            {alert.level}
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
            }}
          >
            {alert.module}
          </span>
          <span className="alert-time">{formatDistanceToNow(alert.timestamp)}</span>
        </div>
      </div>
    </div>
  );
}

function TimelineChart({ data }) {
  const maxEvents = Math.max(...data.map((d) => d.events), 1);
  const maxAlerts = Math.max(...data.map((d) => d.alerts), 1);

  return (
    <div>
      <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div
            style={{ width: 12, height: 3, background: 'var(--accent-primary)', borderRadius: 2 }}
          />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
            EVENTOS
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div
            style={{ width: 12, height: 3, background: 'var(--accent-red)', borderRadius: 2 }}
          />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
            ALERTAS
          </span>
        </div>
      </div>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 8,
          height: 100,
          paddingBottom: 20,
          position: 'relative',
        }}
      >
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map((pct) => (
          <div
            key={pct}
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              bottom: `calc(${pct}% + 20px)`,
              borderBottom: '1px solid var(--border-card)',
              pointerEvents: 'none',
            }}
          />
        ))}
        {data.map((d, i) => (
          <div
            key={i}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 2,
              height: '100%',
              justifyContent: 'flex-end',
            }}
          >
            <div style={{ display: 'flex', gap: 2, alignItems: 'flex-end', height: '80px' }}>
              {/* Events bar */}
              <div
                style={{
                  width: 8,
                  height: `${Math.max(4, (d.events / maxEvents) * 80)}px`,
                  background: 'var(--accent-primary)',
                  opacity: 0.7,
                  borderRadius: '2px 2px 0 0',
                  transition: 'height 0.5s ease',
                }}
              />
              {/* Alerts bar */}
              <div
                style={{
                  width: 8,
                  height: `${Math.max(d.alerts > 0 ? 4 : 0, (d.alerts / maxAlerts) * 80)}px`,
                  background: 'var(--accent-red)',
                  opacity: 0.7,
                  borderRadius: '2px 2px 0 0',
                  transition: 'height 0.5s ease',
                }}
              />
            </div>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 9,
                color: 'var(--text-muted)',
                marginTop: 4,
              }}
            >
              {d.time}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SystemHealth({ status }) {
  const items = [
    {
      label: 'CPU TEMP',
      value: `${status.cpu_temp}°C`,
      pct: (status.cpu_temp / 85) * 100,
      color:
        status.cpu_temp > 70
          ? 'var(--accent-red)'
          : status.cpu_temp > 60
          ? 'var(--accent-amber)'
          : 'var(--accent-green)',
    },
    {
      label: 'CPU USAGE',
      value: `${status.cpu_usage}%`,
      pct: status.cpu_usage,
      color: status.cpu_usage > 80 ? 'var(--accent-red)' : 'var(--accent-primary)',
    },
    {
      label: 'RAM USAGE',
      value: `${status.ram_usage}%`,
      pct: status.ram_usage,
      color: status.ram_usage > 85 ? 'var(--accent-red)' : 'var(--accent-amber)',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {items.map((item) => (
        <div key={item.label}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: 6,
            }}
          >
            <span
              style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}
            >
              {item.label}
            </span>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                color: item.color,
                fontWeight: 500,
              }}
            >
              {item.value}
            </span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${Math.min(100, item.pct)}%`,
                background: item.color,
                opacity: 0.8,
              }}
            />
          </div>
        </div>
      ))}

      <div
        style={{
          marginTop: 8,
          paddingTop: 14,
          borderTop: '1px solid var(--border-card)',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 10,
        }}
      >
        {[
          { label: 'PLATAFORMA', value: 'Raspberry Pi 3B' },
          { label: 'OS', value: 'Raspbian 12' },
          { label: 'IP LOCAL', value: '192.168.1.100' },
          { label: 'SESIÓN', value: status.session_id },
        ].map((info) => (
          <div key={info.label}>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 9,
                color: 'var(--text-muted)',
                marginBottom: 2,
              }}
            >
              {info.label}
            </div>
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 11,
                color: 'var(--text-secondary)',
              }}
            >
              {info.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
