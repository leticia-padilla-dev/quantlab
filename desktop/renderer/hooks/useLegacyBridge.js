import { useEffect, useReducer, useCallback, useState } from 'react';

const defaultWorkspace = { status: 'idle', serverUrl: null, logs: [], error: null, source: null };

/**
 * useLegacyBridge - Hook that provides access to the legacy app.js state
 * and allows React components to trigger updates via function calls.
 * 
 * The legacy app-legacy.js exposes functions and state in the global scope.
 * This hook provides a React-friendly interface to access and modify that state.
 * 
 * NOTE: This assumes app-legacy.js is loaded first and all legacy functions
 * are available in the global scope (not via window. prefix since they're
 * declared at top level in the script).
 * 
 * Returns: {
 *   state: LegacyState,
 *   actions: { openTab, closeTab, setBaseline, toggleCandidate, ... }
 * }
 */
export function useLegacyBridge() {
  const [renderCount, forceUpdate] = useReducer((x) => x + 1, 0);
  const [workspaceState, setWorkspaceState] = useState(null);
  const [lastKnownServerUrl, setLastKnownServerUrl] = useState(null);

  // Get current state from global scope (set by app-legacy.js)
  // eslint-disable-next-line no-undef
  const legacyState = typeof state !== 'undefined' ? state : null;

  useEffect(() => {
    const bridge = window.quantlabDesktop;
    if (!bridge?.getWorkspaceState || !bridge?.onWorkspaceState) {
      return undefined;
    }

    let mounted = true;

    const applyWorkspaceState = (nextWorkspace) => {
      if (nextWorkspace?.serverUrl) setLastKnownServerUrl(nextWorkspace.serverUrl);
      setWorkspaceState(nextWorkspace);
    };

    bridge.getWorkspaceState()
      .then((nextWorkspace) => mounted && applyWorkspaceState(nextWorkspace))
      .catch((err) => {
        console.warn('[useLegacyBridge] Workspace state is not available.', err);
      });

    const unsubscribe = bridge.onWorkspaceState(applyWorkspaceState);

    return () => {
      mounted = false;
      if (typeof unsubscribe === 'function') unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (!lastKnownServerUrl) {
      return undefined;
    }

    const healthUrl = `${lastKnownServerUrl.replace(/\/$/, '')}/api/paper-sessions-health`;
    let cancelled = false;

    const checkHealth = async () => {
      try {
        const response = await fetch(healthUrl, { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        if (!cancelled) {
          setWorkspaceState((current) => ({
            ...(current || defaultWorkspace),
            status: 'ready',
            serverUrl: lastKnownServerUrl,
            error: null,
          }));
        }
      } catch {
        if (!cancelled) {
          setWorkspaceState((current) => ({
            ...(current || defaultWorkspace),
            status: 'error',
            serverUrl: null,
            error: 'Research backend is not reachable',
          }));
        }
      }
    };

    checkHealth();
    const intervalId = window.setInterval(checkHealth, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [lastKnownServerUrl]);

  // Wrapper function to call a global legacy function and trigger re-render
  const callLegacyFunction = useCallback((fnName, ...args) => {
    try {
      const fn = globalThis[fnName];
      if (typeof fn !== 'function') {
        console.warn(`[useLegacyBridge] Legacy function ${fnName} is not available.`);
        return Promise.resolve(null);
      }
      const result = fn(...args);
      // Force React to re-render after legacy function executes
      return Promise.resolve(result).finally(() => setTimeout(forceUpdate, 100));
    } catch (err) {
      console.error(`Error calling legacy function ${fnName}:`, err);
      setTimeout(forceUpdate, 100);
      return Promise.resolve(null);
    }
  }, []);

  // Bridge actions that map to legacy functions (excluding shell state ownership)
  const actions = {
    setBaseline: useCallback(
      (runId) => callLegacyFunction('setBaseline', runId),
      [callLegacyFunction]
    ),
    toggleCandidate: useCallback(
      (runId) => callLegacyFunction('toggleCandidate', runId),
      [callLegacyFunction]
    ),
    toggleShortlist: useCallback(
      (runId) => callLegacyFunction('toggleShortlist', runId),
      [callLegacyFunction]
    ),

    toggleSweepEntry: useCallback(
      (entryOrId) => {
        if (entryOrId && typeof entryOrId === 'object') {
          return callLegacyFunction('toggleSweepDecisionEntry', entryOrId);
        }
        const entryId = typeof entryOrId === 'string' ? entryOrId : null;
        const row = entryId && typeof globalThis.findSweepDecisionRow === 'function'
          ? globalThis.findSweepDecisionRow(entryId)
          : null;
        if (!row) {
          console.warn(`[useLegacyBridge] Sweep row ${entryId || '<missing>'} is not available.`);
          return Promise.resolve(null);
        }
        return callLegacyFunction('toggleSweepDecisionEntry', row);
      },
      [callLegacyFunction]
    ),
    toggleSweepShortlist: useCallback(
      (entryId) => callLegacyFunction('toggleSweepDecisionShortlist', entryId),
      [callLegacyFunction]
    ),
    setSweepBaseline: useCallback(
      (entryId) => callLegacyFunction('setSweepDecisionBaseline', entryId),
      [callLegacyFunction]
    ),
  };

  // Polling removed in #412: React now owns the shell state and
  // persistence. Legacy data is still read on mount or via
  // explicit bridge actions.
  const bridgedState = legacyState
    ? { ...legacyState, workspace: workspaceState ?? legacyState.workspace }
    : { workspace: workspaceState ?? defaultWorkspace };

  return {
    state: bridgedState,
    actions,
  };
}

/**
 * Bridge data accessors that map to legacy functions
 */
export function useLegacyDataAccessors() {
  return {
    getRuns: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getRuns === 'function' ? getRuns() : [];
    }, []),
    
    getLatestRun: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getLatestRun === 'function' ? getLatestRun() : null;
    }, []),
    
    findRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof findRun === 'function' ? findRun(runId) : null;
    }, []),
    
    getSelectedRuns: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getSelectedRuns === 'function' ? getSelectedRuns() : [];
    }, []),
    
    getJobs: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getJobs === 'function' ? getJobs() : [];
    }, []),
    
    getLatestFailedJob: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getLatestFailedJob === 'function' ? getLatestFailedJob() : null;
    }, []),
    
    loadRunDetail: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof loadRunDetail === 'function' ? loadRunDetail(runId) : Promise.resolve(null);
    }, []),
    
    getRunRelatedJobs: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof getRunRelatedJobs === 'function' ? getRunRelatedJobs(runId) : [];
    }, []),
    
    getSweepDecisionEntriesForRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof getSweepDecisionEntriesForRun === 'function' ? getSweepDecisionEntriesForRun(runId) : [];
    }, []),

    findSweepDecisionRow: useCallback((entryId) => {
      // eslint-disable-next-line no-undef
      return typeof findSweepDecisionRow === 'function' ? findSweepDecisionRow(entryId) : null;
    }, []),
  };
}

/**
 * Bridge decision logic that wraps legacy decision functions
 */
export function useLegacyDecision() {
  return {
    isBaselineRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof isBaselineRun === 'function' ? isBaselineRun(runId) : false;
    }, []),
    
    isCandidateRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof isCandidateRun === 'function' ? isCandidateRun(runId) : false;
    }, []),
    
    isShortlistedRun: useCallback((runId) => {
      // eslint-disable-next-line no-undef
      return typeof isShortlistedRun === 'function' ? isShortlistedRun(runId) : false;
    }, []),
    
    getCandidateEntry: useCallback((store, runId) => {
      // eslint-disable-next-line no-undef
      return typeof getCandidateEntry === 'function' ? getCandidateEntry(store, runId) : null;
    }, []),
    
    summarizeCandidateState: useCallback((store, runId) => {
      // eslint-disable-next-line no-undef
      return typeof summarizeCandidateState === 'function' ? summarizeCandidateState(store, runId) : "unknown";
    }, []),

    getCandidateEntriesResolved: useCallback(() => {
      // eslint-disable-next-line no-undef
      return typeof getCandidateEntriesResolved === 'function' ? getCandidateEntriesResolved() : [];
    }, []),
  };
}
