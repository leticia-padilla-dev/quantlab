import React, { createContext, useContext, useMemo, useState, useEffect, useCallback } from 'react';
import {
  useLegacyBridge,
} from '../hooks/useLegacyBridge';
import { useCandidatesStore } from '../hooks/useCandidatesStore.js';
import { useSnapshot } from '../hooks/useSnapshot.js';
import {
  buildMissingCandidateEntry,
  getCandidateEntriesResolved,
  getCandidateEntry,
  getDecisionCompareRunIds as getDecisionCompareRunIdsFromStore,
  getShortlistRunIds,
  isBaselineRun,
  isCandidateRun,
  isShortlistedRun,
  summarizeCandidateState,
} from '../modules/decision-store.js';
import { uniqueRunIds } from '../modules/utils.js';
import { useRegistry } from './RegistryContext';
import { useSweepDecisionStore } from '../hooks/useSweepDecisionStore.js';
import {
  isBaselineSweepEntry,
  isShortlistedSweepEntry,
  isTrackedSweepEntry,
  summarizeSweepDecisionState,
  getSweepDecisionEntriesResolved,
  getSweepDecisionEntries,
} from '../modules/sweep-decision-store.js';
export { RegistryProvider } from './RegistryContext';

const bridge = window.quantlabDesktop;

/**
 * QuantLabContext provides access to the app state, decision logic,
 * and actions for all surface components (Runs, Compare, Candidates).
*
 * Populated by the App.jsx root component; surfaces consume it via useQuantLab().
 */
export const QuantLabContext = createContext(null);

/**
 * Hook to access QuantLab state and actions in any surface component.
 */
export function useQuantLab() {
  const context = useContext(QuantLabContext);
  if (!context) {
    throw new Error(
      'useQuantLab must be called within QuantLabContext.Provider'
    );
  }
  return context;
}

/**
 * Hook that builds the full context value by bridging to legacy state.
 * Use this in App.jsx to populate the QuantLabContext.Provider value.
 */
export function useQuantLabContextValue() {
  const { state: legacyState } = useLegacyBridge();

  // Native registry: authoritative source of run data (#412 B.1)
  const registry = useRegistry();

  // 1. Native workstation shell state (Master)
  const [tabs, setTabs] = useState([]);
  const [activeTabId, setActiveTabId] = useState(null);
  const [selectedRunIds, setSelectedRunIds] = useState([]);
  const [isInitialized, setIsInitialized] = useState(false);

  const findRun = useCallback((runId) => (
    registry.runs.find((r) => r.run_id === runId) || null
  ), [registry.runs]);

  const candidates = useCandidatesStore(legacyState?.candidatesStore, findRun);
  const sweepDecisions = useSweepDecisionStore(legacyState?.sweepDecisionStore);

  // Native snapshot: fires only when Legacy has not populated state.snapshot (#524)
  const serverUrl = legacyState?.workspace?.serverUrl ?? null;
  const nativeSnapshot = useSnapshot(legacyState?.snapshot != null ? null : serverUrl);
  const effectiveSnapshot = legacyState?.snapshot ?? nativeSnapshot.snapshot ?? null;

  // Native job accessors — read from launchControl.jobs in snapshot (#524)
  const getJobs = useCallback(
    () => (Array.isArray(effectiveSnapshot?.launchControl?.jobs)
      ? effectiveSnapshot.launchControl.jobs
      : []),
    [effectiveSnapshot]
  );

  const getLatestFailedJob = useCallback(
    () => getJobs().find((j) => (j.status ?? '').toLowerCase().includes('failed')) ?? null,
    [getJobs]
  );

  const getRunRelatedJobs = useCallback(
    (runId) => getJobs().filter((j) => j.run_id === runId),
    [getJobs]
  );

  const findJob = useCallback(
    (requestId) => getJobs().find((j) => j.request_id === requestId) ?? null,
    [getJobs]
  );

  // 2. Initialize state from persistence layer on mount
  useEffect(() => {
    async function loadInitialState() {
      try {
        const store = await bridge.getShellWorkspaceStore();
        if (store) {
          const loadedTabs = Array.isArray(store.tabs) && store.tabs.length > 0
            ? store.tabs
            : [{
                id: 'paper-ops',
                kind: 'paper',
                navKind: 'paper-ops',
                title: 'Paper Ops',
              }];
          setTabs(loadedTabs);
          setActiveTabId(store.active_tab_id || loadedTabs[0]?.id || null);
          setSelectedRunIds(store.selected_run_ids || []);
        }
      } catch (err) {
        console.error('Failed to load initial workstation state:', err);
      } finally {
        setIsInitialized(true);
      }
    }
    loadInitialState();
  }, []);

  // 3. Centralized persistence: Sync to Electron whenever workstation state changes
  useEffect(() => {
    if (!isInitialized) return;

    const store = {
      version: 1,
      tabs,
      active_tab_id: activeTabId,
      selected_run_ids: selectedRunIds,
      // Note: We don't touch launch_form here yet to keep the slice narrow
    };

    bridge.saveShellWorkspaceStore(store)
      .catch(err => console.error('Failed to persist workstation state:', err));
  }, [tabs, activeTabId, selectedRunIds, isInitialized]);

  // 4. Native actions (Simplified by centralized persistence)
  const openTab = useCallback((kindOrTab, title, requestIdOrRunId) => {
    const normalized = kindOrTab && typeof kindOrTab === 'object'
      ? kindOrTab
      : { kind: kindOrTab, title, requestIdOrRunId };

    const kind = normalized?.kind;
    const tabTitle = normalized?.title || title || `${kind} review`;
    const tabId = typeof normalized?.id === 'string' && normalized.id
      ? normalized.id
      : null;
    const requestId = typeof normalized?.requestId === 'string'
      ? normalized.requestId
      : (typeof requestIdOrRunId === 'string' ? requestIdOrRunId : null);
    const runId = typeof normalized?.runId === 'string'
      ? normalized.runId
      : (typeof requestIdOrRunId === 'string' ? requestIdOrRunId : null);
    const runIds = Array.isArray(normalized?.runIds)
      ? normalized.runIds.map((value) => String(value)).filter(Boolean)
      : [];
    const subview = typeof normalized?.subview === 'string' && normalized.subview
      ? normalized.subview
      : null;

    setTabs(currentTabs => {
      const existing = tabId
        ? currentTabs.find((tab) => tab.id === tabId)
        : currentTabs.find((tab) => {
            if (kind === 'job') return tab.kind === kind && tab.requestId === requestId;
            if (kind === 'run' || kind === 'artifacts') return tab.kind === kind && tab.runId === runId;
            if (kind === 'compare') {
              const currentRunIds = Array.isArray(tab.runIds) ? tab.runIds.map((value) => String(value)) : [];
              return tab.kind === kind && currentRunIds.join('|') === runIds.join('|');
            }
            return tab.kind === kind;
          });

      if (existing) {
        setActiveTabId(existing.id);
        return currentTabs;
      }

      let nextId = tabId || `tab-${Date.now()}`;
      if (kind === 'run') nextId = `run:${runId}`;
      if (kind === 'artifacts') nextId = `artifacts:${runId}`;
      if (kind === 'job') nextId = `job:${requestId}`;
      if (kind === 'compare' && runIds.length) nextId = `compare:${runIds.join('|')}`;
      if (kind === 'compare' && !runIds.length) nextId = tabId || 'compare:selection';

      const newTab = { id: nextId, kind, title: tabTitle };
      if (kind === 'job' && requestId) newTab.requestId = requestId;
      if ((kind === 'run' || kind === 'artifacts') && runId) newTab.runId = runId;
      if (kind === 'compare' && runIds.length) newTab.runIds = runIds;
      if (subview) newTab.subview = subview;

      setActiveTabId(nextId);
      return [...currentTabs, newTab];
    });
  }, []);

  const closeTab = useCallback((tabId) => {
    setTabs(currentTabs => {
      const nextTabs = currentTabs.filter(t => t.id !== tabId);
      if (activeTabId === tabId) {
        setActiveTabId(nextTabs[nextTabs.length - 1]?.id || null);
      }
      return nextTabs;
    });
  }, [activeTabId]);

  const setActiveTab = useCallback((tabId) => {
    setActiveTabId(tabId);
  }, []);

  const navigateToSurface = useCallback((kind) => {
    setTabs(currentTabs => {
      // Logic for selecting the "default" ID for a kind
      // For runs, compare, candidates, paper, system, experiments, it's usually just the kind as ID
      const surfaceIdMap = {
        'runs': 'runs-native', // Match smoke test expectation
        'candidates': 'candidates',
        'compare': 'compare:selection',
        'paper-ops': 'paper-ops',
        'system': 'system',
        'experiments': 'experiments',
        'launch': 'launch'
      };

      const id = surfaceIdMap[kind] || kind;
      const existing = currentTabs.find(t => t.id === id);

      if (existing) {
        setActiveTabId(id);
        return currentTabs;
      }

      // Add new tab if missing
      const titleMap = {
        'runs': 'Runs',
        'candidates': 'Candidates',
        'compare': 'Compare',
        'paper-ops': 'Paper Ops',
        'system': 'System',
        'experiments': 'Experiments',
        'launch': 'Launch'
      };

      const newTab = {
        id,
        kind: kind === 'paper-ops' ? 'paper' : kind,
        navKind: kind,
        title: titleMap[kind] || kind,
      };
      setActiveTabId(id);
      return [...currentTabs, newTab];
    });
  }, []);

  const toggleRunSelection = useCallback((runId) => {
    setSelectedRunIds(current =>
      current.includes(runId)
        ? current.filter(id => id !== runId)
        : [...current, runId]
    );
  }, []);

  const updateTab = useCallback((tabId, patch) => {
    setTabs(currentTabs =>
      currentTabs.map(t => t.id === tabId ? { ...t, ...patch } : t)
    );
  }, []);

  // Native data accessors — read from RegistryContext and native snapshot
  const dataAccessors = useMemo(() => ({
    getRuns: () => registry.runs,
    getLatestRun: () => registry.runs[registry.runs.length - 1] || null,
    findRun,
    getSelectedRuns: () =>
      registry.runs.filter((r) => selectedRunIds.includes(r.run_id)),
    // Native job accessors (replaced legacy delegation via #524)
    getJobs,
    getLatestFailedJob,
    getRunRelatedJobs,
    findJob,
    getSweepDecisionEntriesForRun: (runId) => {
      return getSweepDecisionEntries(sweepDecisions.store).filter(
        (entry) => entry.sweep_run_id === runId
      );
    },
  }), [registry.runs, selectedRunIds, findRun, getJobs, getLatestFailedJob, getRunRelatedJobs, findJob, sweepDecisions.store]);

  const decision = useMemo(() => {
    const store = candidates.store;
    const resolveStoreAndRunId = (storeOrRunId, maybeRunId) => {
      if (maybeRunId === undefined) return { store, runId: storeOrRunId };
      return { store: storeOrRunId || store, runId: maybeRunId };
    };

    return {
      isBaselineRun: (storeOrRunId, maybeRunId) => {
        const resolved = resolveStoreAndRunId(storeOrRunId, maybeRunId);
        return isBaselineRun(resolved.store, resolved.runId);
      },
      isCandidateRun: (storeOrRunId, maybeRunId) => {
        const resolved = resolveStoreAndRunId(storeOrRunId, maybeRunId);
        return isCandidateRun(resolved.store, resolved.runId);
      },
      isShortlistedRun: (storeOrRunId, maybeRunId) => {
        const resolved = resolveStoreAndRunId(storeOrRunId, maybeRunId);
        return isShortlistedRun(resolved.store, resolved.runId);
      },
      getCandidateEntry: (storeOrRunId, maybeRunId) => {
        const resolved = resolveStoreAndRunId(storeOrRunId, maybeRunId);
        return getCandidateEntry(resolved.store, resolved.runId);
      },
      getCandidateEntriesResolved: (storeOrFindRun, maybeFindRun) => {
        const useProvidedStore = storeOrFindRun && typeof storeOrFindRun === 'object';
        const selectedStore = useProvidedStore ? storeOrFindRun : store;
        const selectedFindRun = typeof maybeFindRun === 'function'
          ? maybeFindRun
          : (typeof storeOrFindRun === 'function' ? storeOrFindRun : findRun);
        return getCandidateEntriesResolved(selectedStore, selectedFindRun);
      },
      buildMissingCandidateEntry: (runId) => buildMissingCandidateEntry(runId, findRun),
      getShortlistRunIds: (selectedStore = store, selectedFindRun = findRun) =>
        getShortlistRunIds(selectedStore, selectedFindRun),
      getDecisionCompareRunIds: (
        uniqueRunIdsFn = uniqueRunIds,
        maxCandidateCompare = 4,
        selectedStore = store,
        selectedFindRun = findRun
      ) => getDecisionCompareRunIdsFromStore(
        selectedStore,
        selectedFindRun,
        uniqueRunIdsFn,
        maxCandidateCompare
      ),
      summarizeCandidateState: (storeOrRunId, maybeRunId) => {
        const resolved = resolveStoreAndRunId(storeOrRunId, maybeRunId);
        return summarizeCandidateState(resolved.store, resolved.runId);
      },
    };
  }, [candidates.store, findRun]);

  // Combine native workstation state with legacy snapshot/decision data
  const value = useMemo(
    () => ({
      state: {
        ...(legacyState || {}), // Guard against null legacyState
        snapshot: effectiveSnapshot, // Native snapshot overrides legacy (#524)
        tabs,
        activeTabId,
        selectedRunIds,
        candidatesStore: candidates.store,
        candidatesStoreStatus: candidates.status,
        candidatesStoreError: candidates.error,
        sweepDecisionStore: sweepDecisions.store,
        sweepDecision: {
          isBaseline: isBaselineSweepEntry,
          isShortlisted: isShortlistedSweepEntry,
          isTracked: isTrackedSweepEntry,
          summarizeState: summarizeSweepDecisionState,
          getEntriesResolved: getSweepDecisionEntriesResolved,
        },
        isInitialized,
        // Surface registry health for Topbar / smoke diagnostics
        registryLoading: registry.isLoading,
        registryError: registry.lastError,
      },
      ...dataAccessors,
      decision,
      setBaseline: candidates.setBaseline,
      toggleCandidate: candidates.toggleCandidate,
      toggleShortlist: candidates.toggleShortlist,
      toggleSweepEntry: sweepDecisions.toggleSweepEntry,
      toggleSweepShortlist: sweepDecisions.toggleSweepShortlist,
      setSweepBaseline: sweepDecisions.setSweepBaseline,
      openTab,
      closeTab,
      setActiveTab,
      navigateToSurface,
      refreshRegistry: registry.refreshSnapshot,
      toggleRunSelection,
      updateTab,
    }),
    [legacyState, effectiveSnapshot, tabs, activeTabId, selectedRunIds, candidates, sweepDecisions, isInitialized, registry.isLoading, registry.lastError, registry.refreshSnapshot, dataAccessors, decision, openTab, closeTab, setActiveTab, navigateToSurface, toggleRunSelection, updateTab]
  );

  return value;
}

/**
 * QuantLabContext.Provider wraps the entire app.
 * Value shape:
 * {
 *   state: {
 *     workspace: { status, serverUrl, error, logs },
 *     snapshot: { runsRegistry, launchControl, paperHealth, brokerHealth, stepbitWorkspace },
 *     candidatesStore: { baseline_run_id, candidates: [...] },
 *     selectedRunIds: string[],
 *     tabs: Tab[],
 *     activeTabId: string | null,
 *   },
*
 *   // Data accessors (mirrors legacy ctx functions)
 *   getRuns: () => Run[],
 *   getLatestRun: () => Run | null,
 *   findRun: (runId: string) => Run | null,
 *   getSelectedRuns: () => Run[],
 *   getJobs: () => Job[],
 *   getLatestFailedJob: () => Job | null,
*
 *   // Decision logic (access isCandidateRun, isShortlistedRun, etc.)
 *   decision: {
 *     isBaselineRun: (runId: string) => boolean,
 *     isCandidateRun: (runId: string) => boolean,
 *     isShortlistedRun: (runId: string) => boolean,
 *     getCandidateEntriesResolved: () => CandidateEntry[],
 *   },
 *   // Actions to modify state
 *   setBaseline: (runId: string) => void,
 *   toggleCandidate: (runId: string) => void,
 *   toggleShortlist: (runId: string) => void,
 *   openTab: (tab: Tab) => void,
 *   closeTab: (tabId: string) => void,
 *   setActiveTab: (tabId: string) => void,
 * }
 */
export const QuantLabContextProvider = ({ value, children }) => {
  return (
    <QuantLabContext.Provider value={value}>
      {children}
    </QuantLabContext.Provider>
  );
};
