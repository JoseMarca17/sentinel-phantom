// components/layout/Sidebar.jsx
import { useSocket } from '../../hooks/useSocket';
import { useAlerts } from '../../hooks/usePiData';

const NAV = [
  { id: 'overview',  label: 'Overview',   icon: '◈', section: 'MONITOR' },
  { id: 'alerts',    label: 'Alertas',    icon: '⚠', section: null },
  { id: 'devices',   label: 'Dispositivos', icon: '◉', section: null },
  { id: 'events',    label: 'Eventos',    icon: '≡',  section: null },
  { id: 'modules',   label: 'Módulos',    icon: '⬡',  section: 'CONTROL' },
  { id: 'reports',   label: 'Reportes',   icon: '▤',  section: null },
];

export default function Sidebar({ page, setPage, collapsed, mobileOpen, onToggleCollapse }) {
  const { connected } = useSocket();
  const { data: alerts } = useAlerts();

  const criticalCount = Array.isArray(alerts)
    ? alerts.filter(a => !a.acknowledged && ['CRITICAL','HIGH'].includes(a.severity)).length
    : 0;

  return (
    <nav className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
      {/* Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo-mark">SP</div>
        {!collapsed && (
          <div className="sidebar-logo-text">
            <span>SENTINEL</span> PHANTOM
          </div>
        )}
      </div>

      {/* Nav */}
      <div className="sidebar-nav">
        {NAV.map((item) => (
          <div key={item.id}>
            {item.section && (
              <div className="nav-section-label">{item.section}</div>
            )}
            <div
              className={`nav-item ${page === item.id ? 'active' : ''}`}
              onClick={() => setPage(item.id)}
              title={collapsed ? item.label : undefined}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.id === 'alerts' && criticalCount > 0 && (
                <span className="nav-badge">{criticalCount}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="device-status">
          <div className={`status-dot ${connected ? 'online' : 'offline'}`} />
          {!collapsed && (
            <span>{connected ? 'PI conectada' : 'Sin conexión'}</span>
          )}
        </div>
        {!collapsed && (
          <div style={{ fontSize:'0.62rem', color:'var(--text-muted)' }}>
            EMI Open House 2026
          </div>
        )}
        <button
          className="btn btn-ghost btn-sm btn-icon"
          onClick={onToggleCollapse}
          title={collapsed ? 'Expandir' : 'Colapsar'}
          style={{ marginTop:4, alignSelf:'flex-start' }}
        >
          {collapsed ? '▶' : '◀'}
        </button>
      </div>
    </nav>
  );
}