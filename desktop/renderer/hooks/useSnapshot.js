import { useCallback, useEffect, useRef, useState } from 'react';

const POLL_INTERVAL_MS = 30_000;

const REQUIRED_ENDPOINTS = {
  paperHealth: '/api/paper-sessions-health',
  brokerHealth: '/api/broker-submissions-health',
};

const OPTIONAL_ENDPOINTS = {
  launchControl: '/api/launch-control',
  hyperliquidSurface: '/api/hyperliquid-surface',
};

const INITIAL_STATUS = {
  status: 'idle',
  error: null,
  source: 'none',
  lastSuccessAt: null,
  consecutiveErrors: 0,
};

function errorMessage(reason) {
  if (reason && typeof reason.message === 'string') return reason.message;
  if (typeof reason === 'string') return reason;
  return 'Snapshot endpoint failed';
}

function classifyRequired(results) {
  const failures = Object.entries(results)
    .filter(([, result]) => result.status === 'rejected')
    .map(([key, result]) => ({ key, message: errorMessage(result.reason) }));

  if (!failures.length) return { status: 'ready', error: null, failures };
  if (failures.length < Object.keys(REQUIRED_ENDPOINTS).length) {
    return { status: 'degraded', error: failures[0].message, failures };
  }
  return { status: 'error', error: failures[0].message, failures };
}

export function useSnapshot(serverUrl) {
  const [snapshot, setSnapshot] = useState(null);
  const [snapshotStatus, setSnapshotStatus] = useState(INITIAL_STATUS);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const [endpointErrors, setEndpointErrors] = useState({});
  const consecutiveErrors = useRef(0);

  const refresh = useCallback(async (shouldApply = () => true) => {
    const bridge = window.quantlabDesktop;
    if (typeof bridge?.requestJson !== 'function') {
      if (!shouldApply()) return;
      consecutiveErrors.current += 1;
      const message = 'window.quantlabDesktop.requestJson is unavailable';
      setStatus('error');
      setError(message);
      setEndpointErrors({ bridge: message });
      setSnapshotStatus({
        ...INITIAL_STATUS,
        status: 'error',
        error: message,
        consecutiveErrors: consecutiveErrors.current,
      });
      return;
    }

    const entries = [...Object.entries(REQUIRED_ENDPOINTS), ...Object.entries(OPTIONAL_ENDPOINTS)];
    const settled = await Promise.allSettled(
      entries.map(([, path]) => bridge.requestJson(path))
    );
    if (!shouldApply()) return;
    const results = Object.fromEntries(
      entries.map(([key], index) => [key, settled[index]])
    );
    const requiredResults = Object.fromEntries(
      Object.keys(REQUIRED_ENDPOINTS).map((key) => [key, results[key]])
    );
    const classification = classifyRequired(requiredResults);

    if (classification.status === 'error') {
      consecutiveErrors.current += 1;
    } else {
      consecutiveErrors.current = 0;
    }

    const nextSnapshot = {};
    entries.forEach(([key]) => {
      const result = results[key];
      nextSnapshot[key] = result?.status === 'fulfilled' ? result.value : null;
    });

    const nextEndpointErrors = {};
    entries.forEach(([key]) => {
      const result = results[key];
      if (result?.status === 'rejected') {
        nextEndpointErrors[key] = errorMessage(result.reason);
      }
    });

    const lastSuccessAt = Object.values(results).some((result) => result.status === 'fulfilled')
      ? new Date().toISOString()
      : null;

    setSnapshot(nextSnapshot);
    setStatus(classification.status);
    setError(classification.error);
    setEndpointErrors(nextEndpointErrors);
    setSnapshotStatus({
      status: classification.status === 'ready' ? 'ok' : classification.status,
      error: classification.error,
      source: 'api',
      lastSuccessAt,
      consecutiveErrors: consecutiveErrors.current,
    });
  }, [serverUrl]);

  useEffect(() => {
    let cancelled = false;

    const guardedRefresh = async () => {
      if (cancelled) return;
      await refresh(() => !cancelled);
    };

    guardedRefresh();
    const timer = window.setInterval(guardedRefresh, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [refresh]);

  return {
    snapshot,
    snapshotStatus,
    status,
    error,
    endpointErrors,
    consecutiveErrors: consecutiveErrors.current,
    refresh: () => refresh(),
  };
}
