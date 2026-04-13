import { useState, useEffect, useCallback, useRef } from 'react';

export function usePiData(fetchFn, interval = null, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  const fetch = useCallback(async () => {
    try {
      const res = await fetchFn();
      setData(res.data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Connection error');
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    fetch();
    if (interval) {
      timerRef.current = setInterval(fetch, interval);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetch, interval]);

  return { data, loading, error, refetch: fetch };
}

export default usePiData;
