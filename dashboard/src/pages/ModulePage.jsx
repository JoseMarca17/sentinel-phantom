import { useState, useEffect } from 'react';
import { useParams, useOutletContext } from 'react-router-dom';
import { mockModules, mockEvents } from '../services/mockData';
import { formatDateTime } from '../utils/time';

const MODULE_CONFIG = {
  wifi: {
    label: 'WiFi Táctico',
    color: 'var(--accent-primary)',
    description: 'IDS inalámbrico — detección y ataque sobre redes 802.11',
    hardware: 'MT7601U (modo monitor) + ESP32',
    actions: [
      { id: 'ids_scan', label: 'IDS SCAN', mode: 'defense', desc: 'Detecta deauth, evil twin, beacon flood' },
      { id: 'deauth_attack', label: 'DEAUTH ATTACK', mode: 'offense', desc: 'Envía frames de deautenticación via ESP32' },
      { id: 'evil_twin', label: 'EVIL TWIN', mode: 'offense', desc: 'AP falso con portal cautivo' },
      { id: 'wps_scan', label: 'WPS SCAN', mode: 'recon', desc: 'Enumera APs con WPS activo' },
      { id: 'pmkid', label: 'PMKID CAPTURE', mode: 'offense', desc: 'Captura PMKID para hashcat' },
    ],
    stats: [
      { label: 'APs detectados', value: '14' },
      { label: 'Ataques deauth', value: '120 pkt/s' },
      { label: 'Redes WPS', value: '2' },
      { label: 'Evil Twin', value: '1 activo' },
    ],
  },
  bluetooth: {
    label: 'Bluetooth TSCM',
    color: 'var(--accent-purple)',
    description: 'Escaneo BLE pasivo y detección de dispositivos no autorizados',
    hardware: 'ESP32 (BLE scanner)',
    actions: [
      { id: 'ble_scan', label: 'BLE SCAN', mode: 'defense', desc: 'Escaneo pasivo con OUI lookup' },
      { id: 'ble_disconnect', label: 'BLE DISCONNECT', mode: 'offense', desc: 'Ataque de desconexión BLE' },
      { id: 'spoof', label: 'DEVICE SPOOF', mode: 'offense', desc: 'Suplantación de dispositivo BLE' },
      { id: 'whitelist', label: 'WHITELIST MGR', mode: 'defense', desc: 'Gestión de dispositivos autorizados' },
    ],
    stats: [
      { label: 'Dispositivos BLE', value: '8' },
      { label: 'No autorizados', value: '3' },
      { label: 'En whitelist', value: '5' },
      { label: 'RSSI promedio', value: '-71 dBm' },
    ],
  },
  rfid: {
    label: 'RFID / NFC',
    color: 'var(--accent-green)',
    description: 'Lectura, análisis y clonado de tarjetas MIFARE Classic y 125kHz',
    hardware: 'PN532 (13.56MHz) + RC522 (125kHz)',
    actions: [
      { id: 'read_uid', label: 'LEER UID', mode: 'recon', desc: 'Lee UID de tarjeta MIFARE Classic' },
      { id: 'clone', label: 'CLONAR TARJETA', mode: 'offense', desc: 'Clona tarjeta en < 5 segundos' },
      { id: 'read_125', label: 'LEER 125kHz', mode: 'recon', desc: 'Lectura de tarjetas EM4100 via RC522' },
      { id: 'dump_sectors', label: 'DUMP SECTORES', mode: 'recon', desc: 'Vuelca sectores MIFARE con claves default' },
    ],
    stats: [
      { label: 'Tarjetas leídas', value: '3' },
      { label: 'Clonaciones', value: '1' },
      { label: 'UIDs únicos', value: '3' },
      { label: 'Tipo', value: 'MIFARE Classic' },
    ],
  },
  tscm: {
    label: 'TSCM Espectro',
    color: 'var(--accent-amber)',
    description: 'Detección de cámaras IP ocultas y micrófonos inalámbricos en 2.4GHz',
    hardware: 'MT7601U + nRF24L01',
    actions: [
      { id: 'spectrum_scan', label: 'SPECTRUM SCAN', mode: 'defense', desc: 'Análisis de espectro 2.4GHz completo' },
      { id: 'cam_detect', label: 'DETECT CÁMARAS', mode: 'defense', desc: 'Fingerprinting OUI de cámaras IP ocultas' },
      { id: 'mic_detect', label: 'DETECT MICROS', mode: 'defense', desc: 'Detección de micrófonos inalámbricos' },
      { id: 'report_tscm', label: 'REPORTE TSCM', mode: 'defense', desc: 'Genera reporte de barrido TSCM' },
    ],
    stats: [
      { label: 'Dispositivos 2.4GHz', value: '22' },
      { label: 'Cámaras sospechosas', value: '1' },
      { label: 'OUIs identificados', value: '18' },
      { label: 'Cobertura canal', value: '1-13' },
    ],
  },
  ir: {
    label: 'Infrarrojo',
    color: 'var(--accent-red)',
    description: 'Captura y replay de señales infrarrojas via Raspberry Pi Pico W',
    hardware: 'Raspberry Pi Pico W + receptor IR + LED IR',
    actions: [
      { id: 'capture_ir', label: 'CAPTURAR SEÑAL', mode: 'recon', desc: 'Captura pulsos IR con timestamp' },
      { id: 'replay_ir', label: 'REPLAY SEÑAL', mode: 'offense', desc: 'Retransmite señal capturada' },
      { id: 'list_signals', label: 'VER SEÑALES', mode: 'defense', desc: 'Lista señales capturadas en memoria' },
      { id: 'raw_decode', label: 'DECODIFICAR', mode: 'recon', desc: 'Intenta decodificar protocolo (NEC, RC5)' },
    ],
    stats: [
      { label: 'Señales capturadas', value: '1' },
      { label: 'Replays enviados', value: '0' },
      { label: 'Protocolo', value: 'NEC' },
      { label: 'Hardware', value: 'Pico W' },
    ],
  },
  nrf24: {
    label: 'nRF24 / Drone',
    color: 'var(--accent-green)',
    description: 'Detección de drones por firma RF, MouseJack y triangulación con 2 módulos',
    hardware: '2× nRF24L01 con antena SMA externa',
    actions: [
      { id: 'drone_scan', label: 'DRONE SCAN', mode: 'defense', desc: 'Detecta patrones RF de drones comunes' },
      { id: 'mousejack', label: 'MOUSEJACK', mode: 'offense', desc: 'Ataque MouseJack sobre dispositivos Nordic' },
      { id: 'triangulate', label: 'TRIANGULAR', mode: 'recon', desc: 'Triangulación de señal con 2 módulos nRF24' },
      { id: 'raw_sniff', label: 'RAW SNIFF', mode: 'recon', desc: 'Sniffeo raw en todos los canales 2.4GHz' },
    ],
    stats: [
      { label: 'Señales Nordic', value: '1' },
      { label: 'Drones detectados', value: '0' },
      { label: 'Canales escaneados', value: '125' },
      { label: 'MouseJack targets', value: '0' },
    ],
  },
};

const MODE_STYLE = {
  defense: { color: 'var(--accent-green)', label: 'DEFENSIVO', bg: 'var(--accent-green-dim)' },
  offense: { color: 'var(--accent-red)', label: 'OFENSIVO', bg: 'var(--accent-red-dim)' },
  recon: { color: 'var(--accent-amber)', label: 'RECONOC.', bg: 'var(--accent-amber-dim)' },
};

export default function ModulePage() {
  const { name } = useParams();
  const { setPageTitle } = useOutletContext();
  const [isRunning, setIsRunning] = useState(false);
  const [activeAction, setActiveAction] = useState(null);
  const [log, setLog] = useState([]);

  const config = MODULE_CONFIG[name];
  const moduleData = mockModules.find((m) => m.name === name);
  const moduleEvents = mockEvents.filter((e) => e.module === name);

  useEffect(() => {
    if (config) setPageTitle(config.label.toUpperCase());
  }, [config, setPageTitle]);

  if (!config) {
    return (
      <div className="empty-state" style={{ marginTop: 60 }}>
        // Módulo "{name}" no encontrado
      </div>
    );
  }

  const runAction = (action) => {
    setActiveAction(action.id);
    setIsRunning(true);
    const ts = new Date().toISOString();
    setLog((prev) => [
      {
        ts,
        msg: `[EXEC] ${action.id} — ${action.desc}`,
        type: action.mode,
      },
      ...prev,
    ]);

    // Simulate response after 1.5s
    setTimeout(() => {
      setLog((prev) => [
        {
          ts: new Date().toISOString(),
          msg: `[OK] ${action.id} completado — 0 errores`,
          type: 'ok',
        },
        ...prev,
      ]);
      setIsRunning(false);
      setActiveAction(null);
    }, 1500);
  };

  const stopModule = () => {
    setIsRunning(false);
    setActiveAction(null);
    setLog((prev) => [
      { ts: new Date().toISOString(), msg: '[STOP] Módulo detenido', type: 'warn' },
      ...prev,
    ]);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Module header */}
      <div
        className="card"
        style={{ borderColor: config.color.replace('var(--', '').replace(')', ''), borderLeft: `3px solid ${config.color}` }}
      >
        <div className="card-body" style={{ paddingTop: 16, paddingBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, letterSpacing: 2, color: config.color, margin: 0 }}>
                  {config.label.toUpperCase()}
                </h2>
                <span className={`badge ${moduleData?.status || 'idle'}`}>
                  <span className="badge-dot" />
                  {moduleData?.status || 'idle'}
                </span>
              </div>
              <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
                {config.description}
              </p>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)', margin: '6px 0 0' }}>
                HW: {config.hardware}
              </p>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {isRunning ? (
                <button className="btn btn-danger" onClick={stopModule}>
                  ■ DETENER
                </button>
              ) : (
                <button
                  className="btn btn-success"
                  onClick={() => runAction(config.actions[0])}
                >
                  ▶ INICIAR
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="metric-grid">
        {config.stats.map((stat) => (
          <div className="metric-card" key={stat.label} style={{ '--metric-color': config.color }}>
            <div className="metric-label">{stat.label.toUpperCase()}</div>
            <div className="metric-value" style={{ fontSize: 20, color: config.color }}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Actions */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">ACCIONES DISPONIBLES</span>
          </div>
          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {config.actions.map((action) => {
              const modeStyle = MODE_STYLE[action.mode];
              const isActive = activeAction === action.id;
              return (
                <button
                  key={action.id}
                  onClick={() => runAction(action)}
                  disabled={isRunning}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '10px 14px',
                    background: isActive ? modeStyle.bg : 'var(--bg-panel)',
                    border: `1px solid ${isActive ? modeStyle.color : 'var(--border-base)'}`,
                    borderRadius: 5,
                    cursor: isRunning && !isActive ? 'not-allowed' : 'pointer',
                    opacity: isRunning && !isActive ? 0.5 : 1,
                    textAlign: 'left',
                    transition: 'all var(--t-fast)',
                    width: '100%',
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 9,
                      padding: '2px 6px',
                      borderRadius: 2,
                      background: modeStyle.bg,
                      color: modeStyle.color,
                      border: `1px solid ${modeStyle.color}33`,
                      flexShrink: 0,
                      letterSpacing: 0.5,
                    }}
                  >
                    {modeStyle.label}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: 0.5 }}>
                      {action.label}
                      {isActive && (
                        <span style={{ marginLeft: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: modeStyle.color }}>
                          ● ejecutando...
                        </span>
                      )}
                    </div>
                    <div style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {action.desc}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Terminal log */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">TERMINAL</span>
            <button className="btn btn-ghost btn-sm" onClick={() => setLog([])}>
              LIMPIAR
            </button>
          </div>
          <div
            style={{
              background: 'var(--bg-void)',
              borderTop: '1px solid var(--border-card)',
              height: 280,
              overflowY: 'auto',
              padding: '10px 14px',
              display: 'flex',
              flexDirection: 'column',
              gap: 4,
            }}
          >
            {log.length === 0 ? (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                // Sin actividad — ejecuta una acción
                <span style={{ animation: 'blink 1s infinite', display: 'inline-block', marginLeft: 2 }}>_</span>
              </span>
            ) : (
              log.map((entry, i) => (
                <div key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, display: 'flex', gap: 10 }}>
                  <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>
                    {new Date(entry.ts).toLocaleTimeString('es-BO', { hour12: false })}
                  </span>
                  <span
                    style={{
                      color:
                        entry.type === 'ok'
                          ? 'var(--accent-green)'
                          : entry.type === 'warn'
                          ? 'var(--accent-amber)'
                          : entry.type === 'offense'
                          ? 'var(--accent-red)'
                          : 'var(--accent-primary)',
                    }}
                  >
                    {entry.msg}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent events from this module */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">EVENTOS RECIENTES — {config.label.toUpperCase()}</span>
        </div>
        <div>
          {moduleEvents.length === 0 ? (
            <div className="empty-state">// Sin eventos registrados para este módulo</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>TIPO</th>
                  <th>SEVERIDAD</th>
                  <th>DATA</th>
                  <th>TIMESTAMP</th>
                </tr>
              </thead>
              <tbody>
                {moduleEvents.map((ev) => (
                  <tr key={ev.id}>
                    <td className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {ev.id}
                    </td>
                    <td className="mono" style={{ color: config.color, fontSize: 12 }}>
                      {ev.type}
                    </td>
                    <td>
                      <span className={`badge ${ev.severity}`}>
                        <span className="badge-dot" />
                        {ev.severity}
                      </span>
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)', maxWidth: 260 }}>
                      {Object.entries(ev.data)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(' · ')}
                    </td>
                    <td className="mono" style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {formatDateTime(ev.timestamp)}
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
