// App.jsx
import { useState, useEffect } from 'react';
import Layout      from './components/layout/Layout';
import OverviewPage from './pages/OverviewPage';
import AlertsPage   from './pages/AlertsPage';
import DevicesPage  from './pages/DevicesPage';
import EventsPage   from './pages/EventsPage';
import ModulePage   from './pages/ModulePage';
import ReportsPage  from './pages/ReportsPage';
import './styles/globals.css';
import './styles/layout.css';
import './styles/components.css';

const BOOT_LINES = [
  ['CORE',      'event_bus · logger · config'],
  ['DATABASE',  'SQLite local · SQL Server sync'],
  ['API',       'Flask + SocketIO :5000'],
  ['HARDWARE',  'ESP32 · Pico W · nRF24 · PN532'],
  ['MODULES',   'wifi · bt · rfid · tscm · ir · nrf24'],
  ['DASHBOARD', 'React + Vite · inicializando...'],
];

function BootScreen() {
  const [pct, setPct]       = useState(0);
  const [lineIdx, setLineIdx] = useState(0);

  useEffect(() => {
    const barTimer = setInterval(() => setPct(p => Math.min(p + 2, 100)), 46);
    return () => clearInterval(barTimer);
  }, []);

  useEffect(() => {
    if (lineIdx >= BOOT_LINES.length) return;
    const t = setTimeout(() => setLineIdx(i => i + 1), 480);
    return () => clearTimeout(t);
  }, [lineIdx]);

  return (
    <div className="boot-screen">
      <div className="boot-logo">SENTINEL PHANTOM</div>
      <div className="boot-tag">
        Sistema Portátil de Auditoría Táctica · EMI Open House 2026
      </div>
      <div className="boot-divider" />
      <div className="boot-lines">
        {BOOT_LINES.slice(0, lineIdx + 1).map(([lbl, txt]) => (
          <div key={lbl} className="boot-line">
            <span className="lbl">[{lbl}]</span>
            <span>{txt}</span>
            <span className="ok">OK</span>
          </div>
        ))}
      </div>
      <div className="boot-bar-wrap">
        <div className="boot-bar-track">
          <div className="boot-bar-fill" />
        </div>
        <div className="boot-pct">{pct}%</div>
      </div>
    </div>
  );
}

const PAGES = {
  overview: OverviewPage,
  alerts:   AlertsPage,
  devices:  DevicesPage,
  events:   EventsPage,
  modules:  ModulePage,
  reports:  ReportsPage,
};

export default function App() {
  const [page, setPage]     = useState('overview');
  const [booting, setBooting] = useState(true);
  const Page = PAGES[page] || OverviewPage;

  useEffect(() => {
    const t = setTimeout(() => setBooting(false), 4400);
    return () => clearTimeout(t);
  }, []);

  return (
    <>
      {booting && <BootScreen />}
      <Layout page={page} setPage={setPage}>
        <Page />
      </Layout>
    </>
  );
}