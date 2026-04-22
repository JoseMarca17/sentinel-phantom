// services/api.js
import axios from 'axios';

const PI_BASE = import.meta.env.VITE_PI_API_URL || 'http://192.168.1.50:5000/api';

const api = axios.create({ baseURL: PI_BASE, timeout: 5000 });

export const getHealth   = () => api.get('/health');
export const getEvents   = (p={}) => api.get('/events', { params: p });
export const getAlerts   = (p={}) => api.get('/alerts', { params: p });
export const getDevices  = (p={}) => api.get('/devices', { params: p });
export const getModules  = () => api.get('/modules');
export const startModule = (n) => api.post(`/modules/${n}/start`);
export const stopModule  = (n) => api.post(`/modules/${n}/stop`);
export const ackAlert    = (id) => api.post(`/alerts/${id}/acknowledge`);
export const forceSync   = () => api.post('/modules/sync/force');
export const getSyncStatus = () => api.get('/modules/sync/status');
export const getAlertsSummary = () => api.get('/alerts/summary');
export const getEventStats    = () => api.get('/events/stats');
export const getDeviceStats   = () => api.get('/devices/stats');

export default api;