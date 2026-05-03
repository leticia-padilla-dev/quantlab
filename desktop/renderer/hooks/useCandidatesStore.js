import { useCallback, useEffect, useRef, useState } from 'react';
import {
  defaultCandidatesStore,
  getCandidateEntries,
  getCandidateEntry,
  normalizeCandidatesStore,
} from '../modules/decision-store.js';

const bridge = window.quantlabDesktop;

function nowIso() {
  return new Date().toISOString();
}

function upsertCandidateEntry(store, runId, patch = {}) {
  const existing = getCandidateEntry(store, runId);
  const entries = getCandidateEntries(store).filter((entry) => entry.run_id !== runId);
  entries.push({
    run_id: runId,
    note: existing?.note || '',
    shortlisted: Boolean(existing?.shortlisted),
    created_at: existing?.created_at || nowIso(),
    updated_at: nowIso(),
    ...patch,
  });
  return entries;
}

export function useCandidatesStore(fallbackStore, findRun) {
  const initialStore = normalizeCandidatesStore(fallbackStore || defaultCandidatesStore());
  const [store, setStore] = useState(initialStore);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState(null);
  const storeRef = useRef(initialStore);

  useEffect(() => {
    storeRef.current = store;
  }, [store]);

  useEffect(() => {
    let cancelled = false;

    async function loadStore() {
      try {
        if (typeof bridge?.getCandidatesStore !== 'function') {
          if (!cancelled) {
            setStore(normalizeCandidatesStore(fallbackStore || defaultCandidatesStore()));
            setStatus('fallback');
          }
          return;
        }
        const loaded = normalizeCandidatesStore(await bridge.getCandidatesStore());
        if (!cancelled) {
          setStore(loaded);
          setStatus('ready');
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setStore(normalizeCandidatesStore(fallbackStore || defaultCandidatesStore()));
          setStatus('error');
          setError(err?.message || 'Could not load candidates store.');
        }
      }
    }

    loadStore();
    return () => {
      cancelled = true;
    };
  }, []);

  const persistStore = useCallback(async (nextStore) => {
    const normalized = normalizeCandidatesStore(nextStore);
    storeRef.current = normalized;
    setStore(normalized);
    if (typeof bridge?.saveCandidatesStore !== 'function') {
      setStatus('fallback');
      return normalized;
    }
    try {
      const saved = normalizeCandidatesStore(await bridge.saveCandidatesStore(normalized));
      storeRef.current = saved;
      setStore(saved);
      setStatus('ready');
      setError(null);
      return saved;
    } catch (err) {
      setStatus('error');
      setError(err?.message || 'Could not persist candidates store.');
      return normalized;
    }
  }, []);

  const toggleCandidate = useCallback((runId, forceValue = null) => {
    const normalizedRunId = runId ? String(runId) : null;
    if (!normalizedRunId || (typeof findRun === 'function' && !findRun(normalizedRunId))) {
      setError(`Run ${normalizedRunId || '<missing>'} is not present in the registry snapshot.`);
      return Promise.resolve(null);
    }

    const current = storeRef.current;
    const existing = getCandidateEntry(current, normalizedRunId);
    const shouldExist = forceValue === null ? !existing : Boolean(forceValue);
    const entries = getCandidateEntries(current).filter((entry) => entry.run_id !== normalizedRunId);
    if (shouldExist) {
      entries.push({
        run_id: normalizedRunId,
        note: existing?.note || '',
        shortlisted: Boolean(existing?.shortlisted),
        created_at: existing?.created_at || nowIso(),
        updated_at: nowIso(),
      });
    }

    return persistStore({
      ...current,
      entries,
      baseline_run_id:
        shouldExist || current.baseline_run_id !== normalizedRunId
          ? current.baseline_run_id
          : null,
    });
  }, [findRun, persistStore]);

  const toggleShortlist = useCallback((runId) => {
    const normalizedRunId = runId ? String(runId) : null;
    if (!normalizedRunId || (typeof findRun === 'function' && !findRun(normalizedRunId))) {
      setError(`Run ${normalizedRunId || '<missing>'} is not present in the registry snapshot.`);
      return Promise.resolve(null);
    }

    const current = storeRef.current;
    const existing = getCandidateEntry(current, normalizedRunId);
    const entries = upsertCandidateEntry(current, normalizedRunId, {
      shortlisted: !existing?.shortlisted,
    });
    return persistStore({ ...current, entries });
  }, [findRun, persistStore]);

  const setBaseline = useCallback((runId) => {
    const normalizedRunId = runId ? String(runId) : null;
    const current = storeRef.current;

    if (!normalizedRunId) {
      return persistStore({ ...current, baseline_run_id: null });
    }
    if (typeof findRun === 'function' && !findRun(normalizedRunId)) {
      setError(`Run ${normalizedRunId} is not present in the registry snapshot.`);
      return Promise.resolve(null);
    }

    const nextBaseline = current.baseline_run_id === normalizedRunId ? null : normalizedRunId;
    let entries = getCandidateEntries(current).filter((entry) => entry.run_id !== normalizedRunId);
    const existing = getCandidateEntry(current, normalizedRunId);
    if (nextBaseline) {
      entries = upsertCandidateEntry(current, normalizedRunId);
    } else if (existing) {
      entries.push(existing);
    }
    return persistStore({ ...current, baseline_run_id: nextBaseline, entries });
  }, [findRun, persistStore]);

  return {
    store,
    status,
    error,
    setBaseline,
    toggleCandidate,
    toggleShortlist,
  };
}
