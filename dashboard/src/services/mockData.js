// services/mockData.js — datos de prueba mientras la Pi no esté conectada

export const mockStats = {
  total_events: 1842,
  total_alerts: 47,
  total_devices: 134,
  critical_alerts: 8,
};

export const mockModules = [
  { name: 'wifi',      status: 'RUNNING', uptime: 3720, error_count: 0, enabled: true },
  { name: 'bluetooth', status: 'RUNNING', uptime: 3700, error_count: 0, enabled: true },
  { name: 'rfid',      status: 'STOPPED', uptime: null, error_count: 1, enabled: true },
  { name: 'tscm',      status: 'RUNNING', uptime: 3680, error_count: 0, enabled: true },
  { name: 'ir',        status: 'STOPPED', uptime: null, error_count: 0, enabled: true },
  { name: 'nrf24',     status: 'RUNNING', uptime: 3650, error_count: 2, enabled: true },
];

export const mockAlerts = [
  { id: 1, module: 'wifi',      alert_type: 'DEAUTH_DETECTED',    severity: 'CRITICAL', description: 'Ataque deauth detectado desde MAC A4:C3:F0:12:34:56', timestamp: new Date(Date.now()-120000).toISOString(), device_mac: 'A4:C3:F0:12:34:56', acknowledged: 0 },
  { id: 2, module: 'wifi',      alert_type: 'EVIL_TWIN_DETECTED', severity: 'CRITICAL', description: 'Evil Twin detectado: SSID "EMI-WiFi" en canal 6',       timestamp: new Date(Date.now()-240000).toISOString(), device_mac: 'B8:27:EB:AA:BB:CC', acknowledged: 0 },
  { id: 3, module: 'bluetooth', alert_type: 'UNKNOWN_DEVICE',     severity: 'HIGH',     description: 'Dispositivo BLE no autorizado: iPhone de [unknown]',    timestamp: new Date(Date.now()-600000).toISOString(), device_mac: 'DC:A6:32:11:22:33', acknowledged: 0 },
  { id: 4, module: 'nrf24',     alert_type: 'DRONE_DETECTED',     severity: 'HIGH',     description: 'Señal RF de drone detectada en 2.4GHz',                 timestamp: new Date(Date.now()-900000).toISOString(), device_mac: null,               acknowledged: 0 },
  { id: 5, module: 'tscm',      alert_type: 'HIDDEN_DEVICE',      severity: 'MEDIUM',   description: 'Posible cámara IP oculta: OUI Hikvision',              timestamp: new Date(Date.now()-1800000).toISOString(), device_mac: 'C8:02:8F:AA:BB:CC', acknowledged: 1 },
  { id: 6, module: 'rfid',      alert_type: 'CLONE_ATTEMPT',      severity: 'MEDIUM',   description: 'Intento de clonado MIFARE Classic detectado',           timestamp: new Date(Date.now()-3600000).toISOString(), device_mac: null,               acknowledged: 1 },
  { id: 7, module: 'wifi',      alert_type: 'BEACON_FLOOD',       severity: 'LOW',      description: 'Beacon flood: 248 SSIDs en 30s',                        timestamp: new Date(Date.now()-7200000).toISOString(), device_mac: '00:11:22:33:44:55', acknowledged: 1 },
];

export const mockDevices = [
  { id: 'd1', device_type: 'wifi',      mac: 'A4:C3:F0:12:34:56', vendor: 'Apple Inc.',       ssid: null,       signal_dbm: -62, threat_level: 'CRITICAL', last_seen: new Date(Date.now()-60000).toISOString() },
  { id: 'd2', device_type: 'wifi',      mac: 'B8:27:EB:AA:BB:CC', vendor: 'Raspberry Pi Fdn', ssid: 'EMI-WiFi', signal_dbm: -45, threat_level: 'CRITICAL', last_seen: new Date(Date.now()-120000).toISOString() },
  { id: 'd3', device_type: 'bluetooth', mac: 'DC:A6:32:11:22:33', vendor: 'Apple Inc.',       ssid: null,       signal_dbm: -78, threat_level: 'HIGH',     last_seen: new Date(Date.now()-300000).toISOString() },
  { id: 'd4', device_type: 'wifi',      mac: '74:DA:38:55:66:77', vendor: 'TP-Link',          ssid: 'TP-LINK_5G', signal_dbm: -70, threat_level: 'LOW',   last_seen: new Date(Date.now()-600000).toISOString() },
  { id: 'd5', device_type: 'bluetooth', mac: 'F8:1A:67:88:99:AA', vendor: 'Samsung',          ssid: null,       signal_dbm: -85, threat_level: 'INFO',    last_seen: new Date(Date.now()-900000).toISOString() },
  { id: 'd6', device_type: 'wifi',      mac: 'C8:02:8F:AA:BB:CC', vendor: 'Hikvision',        ssid: null,       signal_dbm: -55, threat_level: 'MEDIUM',  last_seen: new Date(Date.now()-1200000).toISOString() },
];

export const mockEvents = [
  { id: 1, module: 'wifi',      event_type: 'deauth_detected',    timestamp: new Date(Date.now()-120000).toISOString(),  payload: '{"mac":"A4:C3:F0:12:34:56","count":12}' },
  { id: 2, module: 'wifi',      event_type: 'evil_twin_detected', timestamp: new Date(Date.now()-240000).toISOString(),  payload: '{"ssid":"EMI-WiFi","channel":6}' },
  { id: 3, module: 'bluetooth', event_type: 'device_found',       timestamp: new Date(Date.now()-360000).toISOString(),  payload: '{"mac":"DC:A6:32:11:22:33","name":"iPhone"}' },
  { id: 4, module: 'nrf24',     event_type: 'drone_detected',     timestamp: new Date(Date.now()-480000).toISOString(),  payload: '{"freq":2440,"signal":-58}' },
  { id: 5, module: 'wifi',      event_type: 'scan_complete',      timestamp: new Date(Date.now()-600000).toISOString(),  payload: '{"networks":14}' },
  { id: 6, module: 'tscm',      event_type: 'spectrum_scan',      timestamp: new Date(Date.now()-720000).toISOString(),  payload: '{"devices":3}' },
  { id: 7, module: 'rfid',      event_type: 'card_read',          timestamp: new Date(Date.now()-900000).toISOString(),  payload: '{"uid":"DEADBEEF","type":"MIFARE"}' },
  { id: 8, module: 'module',    event_type: 'wifi.started',       timestamp: new Date(Date.now()-3720000).toISOString(), payload: '{"module":"wifi"}' },
];

export const mockSession = {
  id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
  device_id: 'PHANTOM-PI-01',
  started_at: new Date(Date.now()-3720000).toISOString(),
  ended_at: null,
  notes: 'Sesión Open House 2026 — EMI',
};

export const mockHealth = {
  status: 'ok',
  device_id: 'PHANTOM-PI-01',
  device: 'Sentinel Phantom Unit 1',
  modules: { wifi: 'RUNNING', bluetooth: 'RUNNING', rfid: 'STOPPED', tscm: 'RUNNING', ir: 'STOPPED', nrf24: 'RUNNING' },
  db_stats: mockStats,
};