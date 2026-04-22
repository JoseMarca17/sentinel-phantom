// pages/ModulePage.jsx
import { useModules } from '../hooks/usePiData';
import { startModule, stopModule, forceSync } from '../services/api';
import { fmtUptime } from '../utils/time';

const MODULE_DESC = {
  wifi:      'IDS inalámbrico — detección deauth, evil twin, beacon flood. Captura PMKID.',
  bluetooth: 'TSCM BLE — scanning pasivo con OUI lookup, disconnect attack, whitelist.',
  rfid:      'RFID/NFC — lectura UID MIFARE Classic, clonado en <5s, RC522 125kHz.',
  tscm:      'Detector de dispositivos ocultos — cámaras IP, micrófonos via OUI fingerprint.',
  ir:        'Captura y replay de señales infrarrojas via Pico W.',
  nrf24:     'Detección de drones por firma RF, MouseJack, triangulación 2 módulos.',
};

const MOD_ICON = {
  wifi:'📡', bluetooth:'◉', rfid:'◈', tscm:'◆', ir:'◎', nrf24:'△'
};

function ModuleCard({ mod, onStart, onStop }) {
  const isRunning = mod.status === 'RUNNING';
  const isError   = mod.status === 'ERROR';

  return (
    <div className={`module-card ${mod.status.toLowerCase()}`} style={{ animationDelay:`${Math.random()*0.2}s` }}>
      <div className="module-card-top">
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <span style={{ fontSize:'1.3rem' }}>{MOD_ICON[mod.name] || '◦'}</span>
          <div>
            <div className="module-name">{mod.name.toUpperCase()}</div>
            <div className="module-meta">{mod.enabled ? 'habilitado' : 'deshabilitado'}</div>
          </div>
        </div>
        <span className={`mod-chip ${mod.status.toLowerCase()}`}>{mod.status}</span>
      </div>

      <div style={{ fontSize:'0.7rem', color:'var(--text-muted)', lineHeight:1.5 }}>
        {MODULE_DESC[mod.name] || 'Módulo táctico Sentinel Phantom.'}
      </div>

      <div className="module-stats">
        <div className="module-stat">
          <span className="val">{fmtUptime(mod.uptime)}</span>
          <span className="lbl">Uptime</span>
        </div>
        <div className="module-stat">
          <span className="val" style={{ color: mod.error_count > 0 ? 'var(--red)' : 'var(--teal)' }}>
            {mod.error_count}
          </span>
          <span className="lbl">Errores</span>
        </div>
      </div>

      <div className="module-actions">
        {isRunning ? (
          <button className="btn btn-danger btn-sm" onClick={() => onStop(mod.name)}>⏹ Detener</button>
        ) : (
          <button className="btn btn-primary btn-sm" onClick={() => onStart(mod.name)} disabled={!mod.enabled}>
            ▶ Iniciar
          </button>
        )}
      </div>
    </div>
  );
}

export default function ModulePage() {
  const { data, refetch } = useModules();
  const modules = Array.isArray(data) ? data : [];

  const running = modules.filter(m => m.status === 'RUNNING').length;
  const errors  = modules.filter(m => m.status === 'ERROR').length;

  async function handleStart(name) {
    try { await startModule(name); } catch {}
    setTimeout(refetch, 800);
  }
  async function handleStop(name) {
    try { await stopModule(name); } catch {}
    setTimeout(refetch, 800);
  }
  async function handleSync() {
    try { await forceSync(); alert('Sincronización forzada OK'); } catch { alert('Error — Pi no conectada'); }
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <div className="page-title">Control de <span>Módulos</span></div>
          <div className="page-subtitle">
            {running} corriendo · {errors > 0 && <span style={{ color:'var(--red)' }}>{errors} con error · </span>}
            {modules.length} total
          </div>
        </div>
        <div className="page-actions">
          <button className="btn btn-ghost btn-sm" onClick={handleSync}>⇅ Sync forzado</button>
          <button className="btn btn-ghost btn-sm" onClick={refetch}>↻ Actualizar</button>
        </div>
      </div>

      <div className="grid-3" style={{ marginBottom:16 }}>
        {modules.map(m => (
          <ModuleCard key={m.name} mod={m} onStart={handleStart} onStop={handleStop} />
        ))}
        {modules.length === 0 && (
          <div className="empty-state" style={{ gridColumn:'1/-1' }}>
            <div className="empty-icon">⬡</div>
            <div className="empty-text">Pi no conectada — mostrando datos mock</div>
          </div>
        )}
      </div>

      {/* Info de arquitectura */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Arquitectura del <span className="card-title-accent">sistema</span></span>
        </div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(160px,1fr))', gap:10 }}>
          {[
            { label:'Pi 3B', sub:'Cerebro central — Linux', color:'var(--blue-bright)' },
            { label:'ESP32', sub:'WiFi attack + BLE scan', color:'var(--teal)' },
            { label:'Pico W', sub:'IR capture/replay', color:'var(--blue-core)' },
            { label:'nRF24L01', sub:'Detección drones', color:'var(--amber)' },
            { label:'PN532', sub:'NFC/MIFARE RFID', color:'var(--blue-bright)' },
            { label:'SSD1306', sub:'OLED menú físico', color:'var(--teal)' },
          ].map(hw => (
            <div key={hw.label} style={{ background:'var(--bg-elevated)', border:'1px solid var(--border)', borderRadius:'var(--r-md)', padding:'10px 12px' }}>
              <div style={{ fontFamily:'var(--font-display)', fontSize:'0.9rem', fontWeight:600, color:hw.color }}>{hw.label}</div>
              <div style={{ fontSize:'0.65rem', color:'var(--text-muted)', marginTop:3 }}>{hw.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}