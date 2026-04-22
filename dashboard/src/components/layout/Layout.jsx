// components/layout/Layout.jsx
import { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import Topbar  from './Topbar';
import '../../styles/layout.css';

export default function Layout({ children, page, setPage }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed,  setCollapsed]  = useState(false);

  // Cerrar sidebar al cambiar de página en móvil
  useEffect(() => { setMobileOpen(false); }, [page]);

  return (
    <div className="app-shell">
      <Sidebar
        page={page}
        setPage={setPage}
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onToggleCollapse={() => setCollapsed(c => !c)}
      />
      {mobileOpen && (
        <div
          style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.6)', zIndex:99 }}
          onClick={() => setMobileOpen(false)}
        />
      )}
      <div className="main-area">
        <Topbar page={page} onMenuClick={() => setMobileOpen(o => !o)} />
        <div className="page-content">{children}</div>
      </div>
    </div>
  );
}