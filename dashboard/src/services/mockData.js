// Mock data para desarrollo sin hardware Pi
// Reemplazar con llamadas reales a la API cuando la Pi esté disponible

export const mockSystemStatus = {
  pi_online: true,
  uptime: '2h 34m',
  cpu_temp: 58.3,
  cpu_usage: 34,
  ram_usage: 62,
  session_id: 'SES-20260412-001',
  session_start: '2026-04-12T08:00:00Z',
};

export const mockModules = [
  { name: 'wifi', label: 'WiFi Táctico', status: 'active', events_count: 47, icon: '📡' },
  { name: 'bluetooth', label: 'Bluetooth TSCM', status: 'active', events_count: 12, icon: '🔵' },
  { name: 'rfid', label: 'RFID/NFC', status: 'idle', events_count: 3, icon: '💳' },
  { name: 'tscm', label: 'TSCM Espectro', status: 'active', events_count: 8, icon: '📻' },
  { name: 'ir', label: 'Infrarrojo', status: 'idle', events_count: 1, icon: '🔴' },
  { name: 'nrf24', label: 'nRF24 / Drones', status: 'scanning', events_count: 0, icon: '🚁' },
];

export const mockAlerts = [
  { id: 1, level: 'critical', module: 'wifi', message: 'Evil Twin AP detectado: "RedMilitar_Guest"', timestamp: '2026-04-12T09:45:22Z', acked: false },
  { id: 2, level: 'warning', module: 'bluetooth', message: 'Dispositivo BLE desconocido: AA:BB:CC:DD:EE:FF', timestamp: '2026-04-12T09:41:10Z', acked: false },
  { id: 3, level: 'warning', module: 'tscm', message: 'Cámara IP oculta sospechosa en 2.4GHz (OUI: Hikvision)', timestamp: '2026-04-12T09:38:55Z', acked: false },
  { id: 4, level: 'info', module: 'rfid', message: 'MIFARE Classic UID leído: 04:A3:B2:1C', timestamp: '2026-04-12T09:30:00Z', acked: true },
  { id: 5, level: 'critical', module: 'wifi', message: 'Flood de deauth detectado (120 pkts/s) en canal 6', timestamp: '2026-04-12T09:22:11Z', acked: true },
  { id: 6, level: 'info', module: 'nrf24', message: 'Señal 2.4GHz Nordic detectada — posible drone cercano', timestamp: '2026-04-12T09:15:00Z', acked: true },
];

export const mockEvents = [
  { id: 101, type: 'deauth_detected', module: 'wifi', severity: 'high', data: { bssid: 'A0:B1:C2:D3:E4:F5', channel: 6, count: 120 }, timestamp: '2026-04-12T09:45:22Z' },
  { id: 102, type: 'evil_twin', module: 'wifi', severity: 'critical', data: { ssid: 'RedMilitar_Guest', bssid: '00:11:22:33:44:55', signal: -62 }, timestamp: '2026-04-12T09:44:01Z' },
  { id: 103, type: 'ble_device', module: 'bluetooth', severity: 'medium', data: { mac: 'AA:BB:CC:DD:EE:FF', rssi: -78, name: null }, timestamp: '2026-04-12T09:41:10Z' },
  { id: 104, type: 'hidden_camera', module: 'tscm', severity: 'high', data: { oui: 'Hikvision', freq: '2437MHz', signal: -55 }, timestamp: '2026-04-12T09:38:55Z' },
  { id: 105, type: 'rfid_read', module: 'rfid', severity: 'low', data: { uid: '04:A3:B2:1C', type: 'MIFARE Classic' }, timestamp: '2026-04-12T09:30:00Z' },
  { id: 106, type: 'beacon_flood', module: 'wifi', severity: 'high', data: { count: 47, channel: 1 }, timestamp: '2026-04-12T09:28:00Z' },
  { id: 107, type: 'wps_scan', module: 'wifi', severity: 'low', data: { aps_found: 3, wps_enabled: 2 }, timestamp: '2026-04-12T09:20:00Z' },
  { id: 108, type: 'nrf24_signal', module: 'nrf24', severity: 'medium', data: { freq: '2450MHz', pattern: 'Nordic Enhanced Shockburst' }, timestamp: '2026-04-12T09:15:00Z' },
];

export const mockDevices = [
  { id: 1, mac: 'A0:B1:C2:D3:E4:F5', type: 'wifi', vendor: 'Cisco', ssid: 'CorpNet-5G', first_seen: '2026-04-12T08:05:00Z', last_seen: '2026-04-12T09:45:22Z', trusted: false, threat_level: 'high' },
  { id: 2, mac: 'AA:BB:CC:DD:EE:FF', type: 'bluetooth', vendor: 'Unknown', name: null, first_seen: '2026-04-12T09:40:00Z', last_seen: '2026-04-12T09:41:10Z', trusted: false, threat_level: 'medium' },
  { id: 3, mac: 'B4:E6:2D:XX:XX:XX', type: 'wifi', vendor: 'Raspberry Pi', ssid: null, first_seen: '2026-04-12T08:00:00Z', last_seen: '2026-04-12T09:45:00Z', trusted: true, threat_level: 'none' },
  { id: 4, mac: 'FC:EC:DA:XX:XX:XX', type: 'bluetooth', vendor: 'Apple', name: 'iPhone de Oficial', first_seen: '2026-04-12T08:30:00Z', last_seen: '2026-04-12T09:44:00Z', trusted: true, threat_level: 'none' },
  { id: 5, mac: '00:11:22:33:44:55', type: 'wifi', vendor: 'TP-Link', ssid: 'RedMilitar_Guest', first_seen: '2026-04-12T09:43:00Z', last_seen: '2026-04-12T09:45:00Z', trusted: false, threat_level: 'critical' },
];

export const mockTimelineData = [
  { time: '08:00', events: 2, alerts: 0 },
  { time: '08:30', events: 5, alerts: 1 },
  { time: '09:00', events: 8, alerts: 2 },
  { time: '09:15', events: 15, alerts: 3 },
  { time: '09:30', events: 12, alerts: 2 },
  { time: '09:45', events: 22, alerts: 5 },
];

export const mockWifiNetworks = [
  { ssid: 'CorpNet-5G', bssid: 'A0:B1:C2:D3:E4:F5', channel: 36, signal: -45, encryption: 'WPA2', wps: false, suspicious: false },
  { ssid: 'RedMilitar_Guest', bssid: '00:11:22:33:44:55', channel: 6, signal: -62, encryption: 'OPEN', wps: false, suspicious: true },
  { ssid: 'DIRECT-HP-LaserJet', bssid: 'C0:D3:E4:F5:A1:B2', channel: 1, signal: -78, encryption: 'WPA2', wps: true, suspicious: false },
  { ssid: 'EMI-Administrativa', bssid: 'D4:E5:F6:A7:B8:C9', channel: 11, signal: -55, encryption: 'WPA3', wps: false, suspicious: false },
];
