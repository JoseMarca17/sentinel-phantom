import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import OverviewPage from './pages/OverviewPage';
import AlertsPage from './pages/AlertsPage';
import EventsPage from './pages/EventsPage';
import ModulePage from './pages/ModulePage';
import DevicesPage from './pages/DevicesPage';
import ReportsPage from './pages/ReportsPage';
import './styles/globals.css';
import './styles/layout.css';
import './styles/components.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<OverviewPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="modules/:name" element={<ModulePage />} />
          <Route path="devices" element={<DevicesPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
