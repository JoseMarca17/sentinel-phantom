import axios from 'axios';

const PI_BASE_URL = import.meta.env.VITE_PI_API_URL || 'http://192.168.1.100:5000';
const SERVER_BASE_URL = import.meta.env.VITE_SERVER_API_URL || 'http://localhost:5001';

export const piApi = axios.create({
  baseURL: PI_BASE_URL,
  timeout: 5000,
  headers: { 'Content-Type': 'application/json' },
});

export const serverApi = axios.create({
  baseURL: SERVER_BASE_URL,
  timeout: 8000,
  headers: { 'Content-Type': 'application/json' },
});

piApi.interceptors.response.use(
  (res) => res,
  (err) => {
    console.warn('[PI API Error]', err.message);
    return Promise.reject(err);
  }
);

// Events endpoints
export const eventsApi = {
  getAll: (params) => piApi.get('/api/events', { params }),
  getById: (id) => piApi.get(`/api/events/${id}`),
};

// Alerts endpoints
export const alertsApi = {
  getAll: (params) => piApi.get('/api/alerts', { params }),
  acknowledge: (id) => piApi.patch(`/api/alerts/${id}/ack`),
  acknowledgeAll: () => piApi.post('/api/alerts/ack-all'),
};

// Modules endpoints
export const modulesApi = {
  getAll: () => piApi.get('/api/modules'),
  getStatus: (name) => piApi.get(`/api/modules/${name}/status`),
  start: (name) => piApi.post(`/api/modules/${name}/start`),
  stop: (name) => piApi.post(`/api/modules/${name}/stop`),
  getConfig: (name) => piApi.get(`/api/modules/${name}/config`),
  updateConfig: (name, data) => piApi.put(`/api/modules/${name}/config`, data),
};

// Devices endpoints
export const devicesApi = {
  getAll: (params) => piApi.get('/api/devices', { params }),
  getById: (id) => piApi.get(`/api/devices/${id}`),
  whitelist: (id) => piApi.post(`/api/devices/${id}/whitelist`),
  blacklist: (id) => piApi.post(`/api/devices/${id}/blacklist`),
};

// Reports (server)
export const reportsApi = {
  getDailySummary: () => serverApi.get('/api/reports/daily'),
  getTopThreats: () => serverApi.get('/api/reports/threats'),
  getSessions: () => serverApi.get('/api/reports/sessions'),
  exportCsv: () => serverApi.get('/api/export/csv', { responseType: 'blob' }),
};

export default piApi;
