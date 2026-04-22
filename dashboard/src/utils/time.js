// utils/time.js
export function fmtTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
export function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('es-BO', { day: '2-digit', month: '2-digit', year: '2-digit' });
}
export function fmtRelative(iso) {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60)   return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s/60)}m ago`;
  return `${Math.floor(s/3600)}h ago`;
}
export function fmtUptime(seconds) {
  if (!seconds) return '—';
  const h = Math.floor(seconds/3600);
  const m = Math.floor((seconds%3600)/60);
  const s = Math.floor(seconds%60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}
export function nowStr() {
  return new Date().toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}