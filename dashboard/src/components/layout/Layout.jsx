import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { useSocket } from '../../hooks/useSocket';
import { mockAlerts } from '../../services/mockData';
import '../../styles/layout.css';

export default function Layout() {
  const [connectionStatus, setConnectionStatus] = useState('offline');
  const [unackedAlerts, setUnackedAlerts] = useState(
    mockAlerts.filter((a) => !a.acked).length
  );
  const [pageTitle, setPageTitle] = useState('OVERVIEW');

  const { isConnected } = useSocket({
    connect: () => setConnectionStatus('online'),
    disconnect: () => setConnectionStatus('offline'),
    'module:status': (data) => {
      if (data.scanning) setConnectionStatus('scanning');
    },
    'alert:new': () => setUnackedAlerts((n) => n + 1),
    'alert:acked': () => setUnackedAlerts((n) => Math.max(0, n - 1)),
  });

  // Demo: try connecting
  useEffect(() => {
    // In dev without Pi, show offline
    const timer = setTimeout(() => {
      if (!isConnected) setConnectionStatus('offline');
    }, 3000);
    return () => clearTimeout(timer);
  }, [isConnected]);

  return (
    <div className="layout">
      <Sidebar
        connectionStatus={connectionStatus}
        alertCount={unackedAlerts}
      />
      <div className="main-content">
        <Topbar
          title={pageTitle}
          subtitle="SENTINEL PHANTOM"
          sessionId="SES-20260412-001"
        />
        <main className="page-content">
          <Outlet context={{ setPageTitle, setUnackedAlerts }} />
        </main>
      </div>
    </div>
  );
}
