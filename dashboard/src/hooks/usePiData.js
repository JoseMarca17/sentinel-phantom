// hooks/usePiData.js
import { useEffect, useState, useCallback } from 'react';
import * as api from '../services/api';
import * as mock from '../services/mockData';

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export function usePiData(fetcher, mockData, interval = 0) {
  const [data, setData]     = useState(mockData);
  const [loading, setLoading] = useState(!USE_MOCK);
  const [error, setError]   = useState(null);

  const fetch = useCallback(async () => {
    if (USE_MOCK) { setData(mockData); setLoading(false); return; }
    try {
      const res = await fetcher();
      setData(res.data?.data ?? res.data);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    fetch();
    if (interval > 0) {
      const t = setInterval(fetch, interval);
      return () => clearInterval(t);
    }
  }, [fetch, interval]);

  return { data, loading, error, refetch: fetch };
}

export function useHealth()  { return usePiData(() => api.getHealth(),  mock.mockHealth,  10000); }
export function useAlerts()  { return usePiData(() => api.getAlerts({ limit:100 }), mock.mockAlerts, 8000); }
export function useDevices() { return usePiData(() => api.getDevices({ limit:200 }), mock.mockDevices, 15000); }
export function useEvents()  { return usePiData(() => api.getEvents({ limit:100 }),  mock.mockEvents,  8000); }
export function useModules() { return usePiData(() => api.getModules(), mock.mockModules, 10000); }