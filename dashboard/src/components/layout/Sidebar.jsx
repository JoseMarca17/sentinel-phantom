import { NavLink, useLocation } from 'react-router-dom';
import '../../styles/layout.css';

const navItems = [
  {
    section: 'OPERACIONES',
    items: [
      { to: '/', label: 'OVERVIEW', icon: <GridIcon /> },
      { to: '/alerts', label: 'ALERTAS', icon: <AlertIcon />, badgeKey: 'alerts' },
      { to: '/events', label: 'EVENTOS', icon: <EventIcon />, badgeKey: 'events' },
    ],
  },
  {
    section: 'MÓDULOS',
    items: [
      { to: '/modules/wifi', label: 'WIFI TÁCTICO', icon: <WifiIcon /> },
      { to: '/modules/bluetooth', label: 'BLUETOOTH', icon: <BluetoothIcon /> },
      { to: '/modules/rfid', label: 'RFID / NFC', icon: <RfidIcon /> },
      { to: '/modules/tscm', label: 'TSCM', icon: <TscmIcon /> },
      { to: '/modules/ir', label: 'INFRARROJO', icon: <IrIcon /> },
      { to: '/modules/nrf24', label: 'NRF24 / DRONE', icon: <DroneIcon /> },
    ],
  },
  {
    section: 'INTEL',
    items: [
      { to: '/devices', label: 'DISPOSITIVOS', icon: <DeviceIcon /> },
      { to: '/reports', label: 'REPORTES', icon: <ReportIcon /> },
    ],
  },
];

export default function Sidebar({ connectionStatus, alertCount }) {
  const location = useLocation();

  const isActive = (to) => {
    if (to === '/') return location.pathname === '/';
    return location.pathname.startsWith(to);
  };

  const statusLabel = {
    online: 'PI CONECTADA',
    offline: 'PI OFFLINE',
    scanning: 'ESCANEANDO',
  }[connectionStatus] || 'INICIANDO...';

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark">
          <div className="logo-hex">
            <svg viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polygon
                points="18,2 33,10 33,26 18,34 3,26 3,10"
                fill="rgba(0,212,255,0.08)"
                stroke="rgba(0,212,255,0.5)"
                strokeWidth="1"
              />
              <polygon
                points="18,7 28,13 28,23 18,29 8,23 8,13"
                fill="rgba(0,212,255,0.05)"
                stroke="rgba(0,212,255,0.25)"
                strokeWidth="0.5"
              />
              <circle cx="18" cy="18" r="4" fill="rgba(0,212,255,0.6)" />
              <line x1="18" y1="7" x2="18" y2="29" stroke="rgba(0,212,255,0.15)" strokeWidth="0.5" />
              <line x1="8" y1="13" x2="28" y2="23" stroke="rgba(0,212,255,0.15)" strokeWidth="0.5" />
              <line x1="28" y1="13" x2="8" y2="23" stroke="rgba(0,212,255,0.15)" strokeWidth="0.5" />
            </svg>
          </div>
          <div>
            <div className="logo-text">SENTINEL</div>
            <div className="logo-text" style={{ color: 'var(--accent-primary)', marginTop: -2 }}>PHANTOM</div>
            <div className="logo-sub">TACTICAL AUDIT SYS v1.0</div>
          </div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((section) => (
          <div key={section.section}>
            <div className="nav-section-label">{section.section}</div>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={`nav-item ${isActive(item.to) ? 'active' : ''}`}
                style={{ textDecoration: 'none' }}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
                {item.badgeKey === 'alerts' && alertCount > 0 && (
                  <span className="nav-badge">{alertCount}</span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="connection-status">
          <div className={`status-dot ${connectionStatus}`} />
          <span>{statusLabel}</span>
        </div>
        <div style={{ marginTop: 6, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
          192.168.1.100:5000
        </div>
      </div>
    </aside>
  );
}

/* ── Icons (inline SVG minimal) ── */
function GridIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <rect x="1" y="1" width="6" height="6" rx="1" opacity="0.8" />
      <rect x="9" y="1" width="6" height="6" rx="1" opacity="0.8" />
      <rect x="1" y="9" width="6" height="6" rx="1" opacity="0.8" />
      <rect x="9" y="9" width="6" height="6" rx="1" opacity="0.8" />
    </svg>
  );
}
function AlertIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M8 1.5L14.5 13H1.5L8 1.5Z" strokeLinejoin="round" />
      <path d="M8 6v3.5" strokeLinecap="round" />
      <circle cx="8" cy="11" r="0.5" fill="currentColor" />
    </svg>
  );
}
function EventIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="2" y="3" width="12" height="11" rx="1" />
      <path d="M5 1v3M11 1v3M2 7h12" strokeLinecap="round" />
    </svg>
  );
}
function WifiIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M1 5.5C3.5 3 6.5 1.5 8 1.5s4.5 1.5 7 4" strokeLinecap="round" />
      <path d="M3 8c1.3-1.3 3-2 5-2s3.7.7 5 2" strokeLinecap="round" />
      <path d="M5 10.5c.8-.8 1.8-1.3 3-1.3s2.2.5 3 1.3" strokeLinecap="round" />
      <circle cx="8" cy="13" r="1" fill="currentColor" />
    </svg>
  );
}
function BluetoothIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M5 4l6 4-6 4V2l6 4-6 4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function RfidIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="2" y="4" width="12" height="9" rx="1.5" />
      <path d="M5 8h6M5 10.5h3" strokeLinecap="round" />
      <circle cx="11" cy="10.5" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}
function TscmIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="8" cy="8" r="5.5" />
      <circle cx="8" cy="8" r="2.5" />
      <path d="M8 2.5V1M8 15v-1.5M2.5 8H1M15 8h-1.5" strokeLinecap="round" />
    </svg>
  );
}
function IrIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M4 8h8M9 5l3 3-3 3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M2 4v8" strokeLinecap="round" opacity="0.5" />
    </svg>
  );
}
function DroneIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="5.5" y="5.5" width="5" height="5" rx="1" />
      <circle cx="3" cy="3" r="1.5" />
      <circle cx="13" cy="3" r="1.5" />
      <circle cx="3" cy="13" r="1.5" />
      <circle cx="13" cy="13" r="1.5" />
      <path d="M5.5 5.5L4 4M10.5 5.5L12 4M5.5 10.5L4 12M10.5 10.5L12 12" strokeLinecap="round" />
    </svg>
  );
}
function DeviceIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="1" y="3" width="10" height="8" rx="1" />
      <path d="M11 6h3l1 2H11" strokeLinejoin="round" />
      <path d="M3 13h9M7 11v2" strokeLinecap="round" />
    </svg>
  );
}
function ReportIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="3" y="1" width="10" height="14" rx="1" />
      <path d="M6 5h4M6 8h4M6 11h2" strokeLinecap="round" />
    </svg>
  );
}
