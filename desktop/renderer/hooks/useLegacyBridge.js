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

  // Polling removed in #412: React now owns the shell state and
  // persistence. Legacy data is still read on mount or via
  // explicit bridge actions.
  const bridgedState = legacyState
    ? { ...legacyState, workspace: workspaceState ?? legacyState.workspace }
    : { workspace: workspaceState ?? defaultWorkspace };

  return {
    state: bridgedState,
    actions: {},
  };
}


