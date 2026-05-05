import { useCallback, useEffect, useRef, useState } from 'react';
import {
  defaultSweepDecisionStore,
  getSweepDecisionEntries,
  getSweepDecisionEntry,
  normalizeSweepDecisionStore,
} from '../modules/sweep-decision-store.js';

const bridge = window.quantlabDesktop;

function nowIso() {
  return new Date().toISOString();
}

function upsertSweepEntry(store, rowOrId, patch = {}) {
  const entryId = typeof rowOrId === 'string' ? rowOrId : String(rowOrId.entry_id);
  const existing = getSweepDecisionEntry(store, entryId);
  const entries = getSweepDecisionEntries(store).filter((entry) => entry.entry_id !== entryId);
  
  const sweepRunId = typeof rowOrId === 'object' && rowOrId.sweep_run_id 
    ? String(rowOrId.sweep_run_id) 
    : (existing?.sweep_run_id || '');
    
  entries.push({
    entry_id: entryId,
    sweep_run_id: sweepRunId,
    source: existing?.source || (typeof rowOrId === 'object' ? rowOrId.source : 'leaderboard') || 'leaderboard',
    row_index: existing?.row_index ?? (typeof rowOrId === 'object' ? Number(rowOrId.row_index) : 0) ?? 0,
    note: existing?.note || '',
    shortlisted: Boolean(existing?.shortlisted),
    config_path: existing?.config_path || (typeof rowOrId === 'object' ? rowOrId.config_path : '') || '',
    row_snapshot: existing?.row_snapshot || (typeof rowOrId === 'object' ? rowOrId : null),
    created_at: existing?.created_at || nowIso(),
    updated_at: nowIso(),
    ...patch,
  });
  return entries;
}

export function useSweepDecisionStore(fallbackStore) {
  const initialStore = normalizeSweepDecisionStore(fallbackStore || defaultSweepDecisionStore());
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
        if (typeof bridge?.getSweepDecisionStore !== 'function') {
          if (!cancelled) {
            setStore(normalizeSweepDecisionStore(fallbackStore || defaultSweepDecisionStore()));
            setStatus('fallback');
          }
          return;
        }
        const loaded = normalizeSweepDecisionStore(await bridge.getSweepDecisionStore());
        if (!cancelled) {
          setStore(loaded);
          setStatus('ready');
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setStore(normalizeSweepDecisionStore(fallbackStore || defaultSweepDecisionStore()));
          setStatus('error');
          setError(err?.message || 'Could not load sweep decision store.');
        }
      }
    }

    loadStore();
    return () => {
      cancelled = true;
    };
  }, []);

  const persistStore = useCallback(async (nextStore) => {
    const normalized = normalizeSweepDecisionStore(nextStore);
    storeRef.current = normalized;
    setStore(normalized);
    if (typeof bridge?.saveSweepDecisionStore !== 'function') {
      setStatus('fallback');
      return normalized;
    }
    try {
      const saved = normalizeSweepDecisionStore(await bridge.saveSweepDecisionStore(normalized));
      storeRef.current = saved;
      setStore(saved);
      setStatus('ready');
      setError(null);
      return saved;
    } catch (err) {
      setStatus('error');
      setError(err?.message || 'Could not persist sweep decision store.');
      return normalized;
    }
  }, []);

  const toggleSweepEntry = useCallback((rowOrId, forceValue = null) => {
    if (!rowOrId) return Promise.resolve(null);
    const entryId = typeof rowOrId === 'string' ? rowOrId : String(rowOrId.entry_id);

    const current = storeRef.current;
    const existing = getSweepDecisionEntry(current, entryId);
    const shouldExist = forceValue === null ? !existing : Boolean(forceValue);
    const entries = getSweepDecisionEntries(current).filter((entry) => entry.entry_id !== entryId);
    
    if (shouldExist) {
      const newEntries = upsertSweepEntry(current, rowOrId);
      entries.push(newEntries[newEntries.length - 1]);
    }

    return persistStore({
      ...current,
      entries,
      baseline_entry_id:
        shouldExist || current.baseline_entry_id !== entryId
          ? current.baseline_entry_id
          : null,
    });
  }, [persistStore]);

  const toggleSweepShortlist = useCallback((entryId) => {
    if (!entryId) return Promise.resolve(null);
    const normalizedId = String(entryId);

    const current = storeRef.current;
    const existing = getSweepDecisionEntry(current, normalizedId);
    if (!existing) return Promise.resolve(null);
    
    const entries = upsertSweepEntry(current, normalizedId, {
      shortlisted: !existing.shortlisted,
    });
    return persistStore({ ...current, entries });
  }, [persistStore]);

  const setSweepBaseline = useCallback((entryId) => {
    const normalizedId = entryId ? String(entryId) : null;
    const current = storeRef.current;

    if (!normalizedId) {
      return persistStore({ ...current, baseline_entry_id: null });
    }

    const nextBaseline = current.baseline_entry_id === normalizedId ? null : normalizedId;
    let entries = getSweepDecisionEntries(current).filter((entry) => entry.entry_id !== normalizedId);
    const existing = getSweepDecisionEntry(current, normalizedId);
    
    if (existing) {
      entries = upsertSweepEntry(current, normalizedId);
    }
    
    return persistStore({ ...current, baseline_entry_id: nextBaseline, entries });
  }, [persistStore]);

  return {
    store,
    status,
    error,
    setSweepBaseline,
    toggleSweepEntry,
    toggleSweepShortlist,
  };
}

