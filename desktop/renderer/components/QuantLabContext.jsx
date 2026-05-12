// @ts-nocheck -- legacy JS file, not migrated to strict TypeScript. See #462.

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
} from 'react';
import * as decisionStore from '../modules/decision-store.js';
import * as sweepDecisionStore from '../modules/sweep-decision-store.js';
import { buildRunArtifactHref, uniqueRunIds } from '../modules/utils.js';
import { useQuantLabStore } from '../store/quantlabStore.ts';
export { RegistryProvider } from './RegistryContext';

const CONFIG = {
  runsIndexPath: '/outputs/runs/runs_index.json',
  localRunsIndexPath: 'outputs/runs/runs_index.json',
  launchControlPath: '/api/launch-control',
  paperHealthPath: '/api/paper-sessions-health',
  brokerHealthPath: '/api/broker-submissions-health',
  stepbitWorkspacePath: '/api/stepbit-workspace',
  detailArtifacts: ['report.json', 'run_report.json'],
  experimentsConfigDir: 'configs/experiments',
  sweepsOutputDir: 'outputs/sweeps',
  maxCandidateCompare: 4,
  maxExperimentsConfigs: 12,
  maxRecentSweeps: 8,
};

/**
 * QuantLabContext provides the React runtime with state, data accessors,
 * and actions without depending on app-legacy.js globals.
 */
export const QuantLabContext = createContext(null);

export function useQuantLab() {
  const context = useContext(QuantLabContext);
  if (!context) {
    throw new Error('useQuantLab must be called within QuantLabContext.Provider');
  }
  return context;
}

export const useQuantLabContext = useQuantLab;

function getBridge() {
  return window.quantlabDesktop;
}

// Valid kinds from shared/models/tab.ts — kept in sync manually.
const VALID_TAB_KINDS = new Set([
  'runs', 'run', 'artifacts', 'compare', 'candidates',
  'system', 'experiments', 'paper', 'job', 'assistant', 'launch', 'hypothesis',
]);

/**
 * Guards against stale or unknown tab kinds from future persistence.
 * Drops tabs whose kind is not in the current union; maps known legacy aliases.
 */
function rehydrateTabs(rawTabs) {
  if (!Array.isArray(rawTabs)) return [];
  return rawTabs
    .map((tab) => {
      if (!tab || typeof tab !== 'object') return null;
      if (tab.kind === 'shortlist-compare') return { ...tab, kind: 'compare' };
      if (tab.kind === 'ops') return { ...tab, kind: 'paper' };
      return tab;
    })
    .filter((tab) => tab && VALID_TAB_KINDS.has(tab.kind));
}

function normalizeRunsRegistry(registry) {
  if (Array.isArray(registry)) return { runs: registry };
  if (registry && typeof registry === 'object') {
    return {
      ...registry,
      runs: Array.isArray(registry.runs) ? registry.runs : [],
    };
  }
  return { runs: [] };
}

function createSnapshotStatus(source, error = null) {
  if (error) {
    return {
      status: 'degraded',
      error: error.message || String(error),
      source,
      lastSuccessAt: null,
      consecutiveErrors: 1,
      refreshPaused: false,
    };
  }
  if (source === 'none') {
    return {
      status: 'idle',
      error: null,
      source,
      lastSuccessAt: null,
      consecutiveErrors: 0,
      refreshPaused: false,
    };
  }
  return {
    status: 'ok',
    error: null,
    source,
    lastSuccessAt: new Date().toISOString(),
    consecutiveErrors: 0,
    refreshPaused: false,
  };
}

function joinProjectPath(basePath, fileName) {
  const base = String(basePath || '').replace(/[\\/]+$/, '');
  return `${base}\\${fileName}`;
}

async function readOptionalJson(targetPath) {
  try {
    return await getBridge().readProjectJson(targetPath);
  } catch (_error) {
    return null;
  }
}

async function requestOptionalJson(relativePath) {
  try {
    return await getBridge().requestJson(relativePath);
  } catch (_error) {
    return null;
  }
}

async function requestOptionalText(relativePath) {
  if (!relativePath) return '';
  try {
    return await getBridge().requestText(relativePath);
  } catch (_error) {
    return '';
  }
}

async function loadRunsRegistry(workspace) {
  let source = 'none';
  let primaryError = null;

  if (workspace?.serverUrl) {
    try {
      const runsRegistry = normalizeRunsRegistry(
        await getBridge().requestJson(CONFIG.runsIndexPath)
      );
      return { runsRegistry, source: 'api', primaryError: null };
    } catch (error) {
      primaryError = error;
    }
  }

  try {
    const runsRegistry = normalizeRunsRegistry(
      await getBridge().readProjectJson(CONFIG.localRunsIndexPath)
    );
    source = 'local';
    return { runsRegistry, source, primaryError };
  } catch (error) {
    return { runsRegistry: { runs: [] }, source, primaryError: primaryError || error };
  }
}

async function loadSnapshot(workspace) {
  const { runsRegistry, source, primaryError } = await loadRunsRegistry(workspace);
  const canRequestApi = Boolean(workspace?.serverUrl);

  const [launchControl, paperHealth, brokerHealth, stepbitWorkspace] = canRequestApi
    ? await Promise.all([
        requestOptionalJson(CONFIG.launchControlPath),
        requestOptionalJson(CONFIG.paperHealthPath),
        requestOptionalJson(CONFIG.brokerHealthPath),
        requestOptionalJson(CONFIG.stepbitWorkspacePath),
      ])
    : [null, null, null, null];

  return {
    snapshot: {
      runsRegistry,
      launchControl: launchControl || { jobs: [] },
      paperHealth: paperHealth || null,
      brokerHealth: brokerHealth || null,
      stepbitWorkspace: stepbitWorkspace || null,
    },
    snapshotStatus: createSnapshotStatus(source, primaryError),
  };
}

async function loadExperimentsWorkspace() {
  try {
    const [configsListing, sweepsListing] = await Promise.all([
      getBridge().listDirectory(CONFIG.experimentsConfigDir, 0),
      getBridge().listDirectory(CONFIG.sweepsOutputDir, 0),
    ]);

    const configs = (configsListing.entries || [])
      .filter((entry) => entry.kind === 'file' && /\.ya?ml$/i.test(entry.name))
      .sort((left, right) => String(right.modified_at || '').localeCompare(String(left.modified_at || '')))
      .slice(0, CONFIG.maxExperimentsConfigs)
      .map((entry) => ({
        name: entry.name,
        path: entry.path,
        relativePath: entry.relative_path || entry.name,
        modifiedAt: entry.modified_at,
        sizeBytes: entry.size_bytes,
        previewText: '',
      }));

    const sweeps = (sweepsListing.entries || [])
      .filter((entry) => entry.kind === 'directory' && entry.depth === 0)
      .sort((left, right) => String(right.modified_at || '').localeCompare(String(left.modified_at || '')))
      .slice(0, CONFIG.maxRecentSweeps)
      .map((entry) => ({
        run_id: entry.name,
        path: entry.path,
        mode: 'sweep',
        configPath: '',
        configName: '',
        decisionRows: [],
        hasStructuredData: false,
      }));

    return {
      status: 'ready',
      configs,
      sweeps,
      error: null,
      updatedAt: new Date().toISOString(),
    };
  } catch (error) {
    return {
      status: 'error',
      configs: [],
      sweeps: [],
      error: error.message || String(error),
      updatedAt: new Date().toISOString(),
    };
  }
}

function buildCandidateEntry(runId, existing = null) {
  const now = new Date().toISOString();
  return {
    run_id: runId,
    note: existing?.note || '',
    shortlisted: Boolean(existing?.shortlisted),
    created_at: existing?.created_at || now,
    updated_at: now,
  };
}

export function useQuantLabContextValue() {
  // ── Zustand store (replaces the single useState from prior implementation) ──
  const storeState = useQuantLabStore();

  // ── Derived selectors ──────────────────────────────────────────────────────

  const getRuns = useCallback(() => {
    return Array.isArray(storeState.snapshot?.runsRegistry?.runs)
      ? storeState.snapshot.runsRegistry.runs
      : [];
  }, [storeState.snapshot]);

  const findRun = useCallback((runId) => {
    return getRuns().find((run) => run.run_id === runId) || null;
  }, [getRuns]);

  const getJobs = useCallback(() => {
    return Array.isArray(storeState.snapshot?.launchControl?.jobs)
      ? storeState.snapshot.launchControl.jobs
      : [];
  }, [storeState.snapshot]);

  const findJob = useCallback((requestId) => {
    return getJobs().find((job) => job.request_id === requestId) || null;
  }, [getJobs]);

  const getLatestRun = useCallback(() => getRuns()[0] || null, [getRuns]);

  const getLatestFailedJob = useCallback(() => {
    return getJobs().find((job) => job.status === 'failed') || null;
  }, [getJobs]);

  const getSelectedRuns = useCallback(() => {
    return storeState.selectedRunIds.map(findRun).filter(Boolean);
  }, [storeState.selectedRunIds, findRun]);

  const findSweepDecisionRow = useCallback((entryId) => {
    for (const sweep of storeState.experimentsWorkspace.sweeps || []) {
      const row = (sweep.decisionRows || []).find((item) => item.entry_id === entryId);
      if (row) return { ...row, sweep };
    }
    return null;
  }, [storeState.experimentsWorkspace]);

  const decision = useMemo(() => ({
    getCandidateEntry: (storeOrRunId, maybeRunId) => {
      const cs = maybeRunId ? storeOrRunId : storeState.candidatesStore;
      const runId = maybeRunId || storeOrRunId;
      return decisionStore.getCandidateEntry(cs, runId);
    },
    getCandidateEntryResolved: (runId) =>
      decisionStore.getCandidateEntryResolved(storeState.candidatesStore, runId, findRun),
    getCandidateEntriesResolved: () =>
      decisionStore.getCandidateEntriesResolved(storeState.candidatesStore, findRun),
    buildMissingCandidateEntry: (runId) =>
      decisionStore.buildMissingCandidateEntry(runId, findRun),
    isCandidateRun: (runId) =>
      decisionStore.isCandidateRun(storeState.candidatesStore, runId),
    isShortlistedRun: (runId) =>
      decisionStore.isShortlistedRun(storeState.candidatesStore, runId),
    isBaselineRun: (runId) =>
      decisionStore.isBaselineRun(storeState.candidatesStore, runId),
    getDecisionCompareRunIds: () =>
      decisionStore.getDecisionCompareRunIds(
        storeState.candidatesStore,
        findRun,
        uniqueRunIds,
        CONFIG.maxCandidateCompare
      ),
    summarizeCandidateState: (storeOrRunId, maybeRunId) => {
      const cs = maybeRunId ? storeOrRunId : storeState.candidatesStore;
      const runId = maybeRunId || storeOrRunId;
      return decisionStore.summarizeCandidateState(cs, runId);
    },
  }), [storeState.candidatesStore, findRun]);

  const sweepDecision = useMemo(() => ({
    getEntriesResolved: (s, findLiveRow) =>
      sweepDecisionStore.getSweepDecisionEntriesResolved(s, findLiveRow),
    getEntry: (s, entryId) =>
      sweepDecisionStore.getSweepDecisionEntry(s, entryId),
    isTracked: (s, entryId) =>
      sweepDecisionStore.isTrackedSweepEntry(s, entryId),
    isShortlisted: (s, entryId) =>
      sweepDecisionStore.isShortlistedSweepEntry(s, entryId),
    isBaseline: (s, entryId) =>
      sweepDecisionStore.isBaselineSweepEntry(s, entryId),
    summarizeState: (s, entryId) =>
      sweepDecisionStore.summarizeSweepDecisionState(s, entryId),
  }), []);

  const getSweepDecisionEntriesForRun = useCallback((runId) => {
    return sweepDecisionStore
      .getSweepDecisionEntriesResolved(storeState.sweepDecisionStore, findSweepDecisionRow)
      .filter((entry) => entry.sweep_run_id === runId);
  }, [storeState.sweepDecisionStore, findSweepDecisionRow]);

  const getRunRelatedJobs = useCallback((runId) => {
    return getJobs().filter((job) => {
      const payload = job.payload || job.request || {};
      const params = payload.params || payload;
      return (
        job.run_id === runId ||
        job.linked_run_id === runId ||
        params.run_id === runId ||
        params.out_dir === runId
      );
    });
  }, [getJobs]);

  // ── Tab mutations (delegate to store) ─────────────────────────────────────

  const upsertTab = useCallback((tab) => {
    useQuantLabStore.getState().upsertTab(tab);
  }, []);

  const closeTab = useCallback((tabId) => {
    useQuantLabStore.getState().removeTab(tabId);
  }, []);

  const setActiveTab = useCallback((tabId) => {
    useQuantLabStore.getState().setActiveTabId(tabId);
  }, []);

  const toggleRunSelection = useCallback((runId) => {
    useQuantLabStore.getState().toggleRunInSelection(runId);
  }, []);

  // ── Run detail loading ─────────────────────────────────────────────────────

  const loadRunDetail = useCallback(async (runId) => {
    const run = findRun(runId);
    if (!run?.path) throw new Error(`Run ${runId} has no accessible artifact path.`);
    let detail = {
      report: null,
      reportUrl: null,
      directoryEntries: [],
      directoryTruncated: false,
    };

    for (const artifact of CONFIG.detailArtifacts) {
      const localArtifactPath = joinProjectPath(run.path, artifact);
      const href = buildRunArtifactHref(run.path, artifact);
      const localReport = await readOptionalJson(localArtifactPath);
      if (localReport) {
        detail = { ...detail, report: localReport, reportUrl: href || localArtifactPath };
        break;
      }
      if (href) {
        const remoteReport = await requestOptionalJson(href);
        if (remoteReport) {
          detail = { ...detail, report: remoteReport, reportUrl: href };
          break;
        }
      }
    }

    try {
      const listing = await getBridge().listDirectory(run.path, 2);
      detail.directoryEntries = listing.entries || [];
      detail.directoryTruncated = Boolean(listing.truncated);
    } catch (_error) {
      // Directory listing is optional evidence, not a hard runtime dependency.
    }

    return detail;
  }, [findRun]);

  // ── Async tab-open actions ─────────────────────────────────────────────────

  const openRunDetailTab = useCallback(async (runId, options = {}) => {
    if (!runId) return;
    const run = findRun(runId);
    if (!run) return;
    const subview = options.subview || '';
    const tabId = `run:${runId}`;
    const title = subview === 'artifacts' ? `Artifacts: ${run.run_id}` : `Run ${run.run_id}`;
    upsertTab({
      id: tabId,
      kind: 'run',
      navKind: 'runs',
      title,
      runId,
      subview,
      status: 'loading',
      detail: null,
      error: null,
    });
    try {
      const detail = await loadRunDetail(runId);
      upsertTab({
        id: tabId,
        kind: 'run',
        navKind: 'runs',
        title,
        runId,
        subview,
        status: 'ready',
        detail,
        error: null,
      });
    } catch (error) {
      upsertTab({
        id: tabId,
        kind: 'run',
        navKind: 'runs',
        title,
        runId,
        subview,
        status: 'error',
        detail: null,
        error: error.message || String(error),
      });
    }
  }, [findRun, loadRunDetail, upsertTab]);

  const openCompareSelectionTab = useCallback((runIds, label = 'selected runs') => {
    const ids = uniqueRunIds(runIds || []).filter((runId) => findRun(runId));
    if (ids.length < 2) return;
    upsertTab({
      id: `compare:${ids.join('|')}`,
      kind: 'compare',
      navKind: 'compare',
      title: `Compare: ${label}`,
      runIds: ids,
      status: 'loading',
    });
  }, [findRun, upsertTab]);

  const refreshJobTab = useCallback(async (requestId, fallbackJob = null) => {
    if (!requestId) return;
    const job = findJob(requestId) || fallbackJob;
    if (!job) return;
    const tabId = `job:${requestId}`;

    try {
      const [stdoutText, stderrText] = await Promise.all([
        requestOptionalText(job.stdout_href),
        requestOptionalText(job.stderr_href),
      ]);
      upsertTab({
        id: tabId,
        kind: 'job',
        navKind: 'launch',
        title: `Job ${requestId}`,
        requestId,
        jobId: requestId,
        status: 'ready',
        job: findJob(requestId) || job,
        stdoutText,
        stderrText,
        error: null,
      });
    } catch (error) {
      upsertTab({
        id: tabId,
        kind: 'job',
        navKind: 'launch',
        title: `Job ${requestId}`,
        requestId,
        jobId: requestId,
        status: 'error',
        job,
        stdoutText: '',
        stderrText: '',
        error: error.message || 'Could not load job logs.',
      });
    }
  }, [findJob, upsertTab]);

  const openJobTab = useCallback(async (requestId) => {
    if (!requestId) return;
    const job = findJob(requestId);
    if (!job) return;
    const tabId = `job:${requestId}`;
    upsertTab({
      id: tabId,
      kind: 'job',
      navKind: 'launch',
      title: `Job ${requestId}`,
      requestId,
      jobId: requestId,
      status: 'loading',
      job,
      stdoutText: '',
      stderrText: '',
      error: null,
    });
    await refreshJobTab(requestId, job);
  }, [findJob, refreshJobTab, upsertTab]);

  /**
   * openTab — unified tab-open API.
   *
   * State is read from the store via getState() so this callback is stable —
   * experimentsWorkspace and selectedRunIds are no longer in the dependency array.
   */
  const openTab = useCallback((kindOrTab, arg, href) => {
    const isObj = kindOrTab !== null && typeof kindOrTab === 'object';
    const kind = isObj ? kindOrTab.kind : kindOrTab;

    if (kind === 'run') {
      const runId = isObj ? kindOrTab.runId : arg;
      if (!runId) return;
      openRunDetailTab(runId);
      return;
    }
    if (kind === 'artifacts') {
      const runId = isObj ? kindOrTab.runId : arg;
      if (!runId) return;
      openRunDetailTab(runId, { subview: 'artifacts' });
      return;
    }
    if (kind === 'compare') {
      const runIds = isObj && Array.isArray(kindOrTab.runIds)
        ? kindOrTab.runIds
        : useQuantLabStore.getState().selectedRunIds;
      const label = (isObj && kindOrTab.label) || 'selected runs';
      openCompareSelectionTab(runIds, label);
      return;
    }
    if (kind === 'job') {
      const requestId = isObj ? kindOrTab.requestId : arg;
      if (!requestId) return;
      openJobTab(requestId);
      return;
    }

    // Surface tabs — read experimentsWorkspace from store so this callback never stales
    const { experimentsWorkspace } = useQuantLabStore.getState();
    const surfaceTabs = {
      system: { id: 'system', kind: 'system', navKind: 'system', title: 'System' },
      experiments: {
        id: 'experiments',
        kind: 'experiments',
        navKind: 'experiments',
        title: 'Experiments',
        selectedConfigPath: experimentsWorkspace.configs[0]?.path || null,
        selectedSweepId: experimentsWorkspace.sweeps[0]?.run_id || null,
      },
      launch: {
        id: 'launch',
        kind: 'launch',
        navKind: 'launch',
        title: (isObj ? kindOrTab.title : arg) || 'Launch',
        href: isObj ? kindOrTab.href : href,
      },
      hypothesis: {
        id: 'hypothesis',
        kind: 'hypothesis',
        navKind: 'hypothesis',
        title: 'Hypothesis Builder',
      },
      runs: { id: 'runs-native', kind: 'runs', navKind: 'runs', title: 'Runs' },
      candidates: {
        id: 'candidates',
        kind: 'candidates',
        navKind: 'candidates',
        title: 'Candidates',
      },
      paper: {
        id: 'paper-ops',
        kind: 'paper',
        navKind: 'paper-ops',
        title: 'Paper Ops',
      },
      'paper-ops': {
        id: 'paper-ops',
        kind: 'paper',
        navKind: 'paper-ops',
        title: 'Paper Ops',
      },
      assistant: {
        id: 'assistant',
        kind: 'assistant',
        navKind: 'assistant',
        title: 'Assistant',
      },
    };

    const tab = surfaceTabs[kind];
    if (tab) upsertTab(tab);
  }, [openCompareSelectionTab, openJobTab, openRunDetailTab, upsertTab]);

  // ── Persistence actions ────────────────────────────────────────────────────

  const saveCandidatesStore = useCallback(async (nextStore) => {
    const normalized = decisionStore.normalizeCandidatesStore(nextStore);
    useQuantLabStore.getState().applyCandidatesStore(normalized);
    try {
      const persisted = decisionStore.normalizeCandidatesStore(
        await getBridge().saveCandidatesStore(normalized)
      );
      useQuantLabStore.getState().applyCandidatesStore(persisted);
    } catch (_error) {
      // Keep optimistic local decision state if persistence is temporarily unavailable.
    }
  }, []);

  const toggleCandidate = useCallback(async (runId, forceValue = null) => {
    const { candidatesStore: cs } = useQuantLabStore.getState();
    const existing = decisionStore.getCandidateEntry(cs, runId);
    const shouldExist = forceValue === null ? !existing : Boolean(forceValue);
    const entries = decisionStore
      .getCandidateEntries(cs)
      .filter((entry) => entry.run_id !== runId);
    if (shouldExist) entries.push(buildCandidateEntry(runId, existing));
    await saveCandidatesStore({
      ...cs,
      entries,
      baseline_run_id:
        shouldExist || cs.baseline_run_id !== runId
          ? cs.baseline_run_id
          : null,
      updated_at: new Date().toISOString(),
    });
  }, [saveCandidatesStore]);

  const toggleShortlist = useCallback(async (runId) => {
    const { candidatesStore: cs } = useQuantLabStore.getState();
    const existing = decisionStore.getCandidateEntry(cs, runId);
    const entries = decisionStore
      .getCandidateEntries(cs)
      .filter((entry) => entry.run_id !== runId);
    entries.push({
      ...buildCandidateEntry(runId, existing),
      shortlisted: !existing?.shortlisted,
    });
    await saveCandidatesStore({
      ...cs,
      entries,
      updated_at: new Date().toISOString(),
    });
  }, [saveCandidatesStore]);

  const setBaseline = useCallback(async (runId) => {
    const { candidatesStore: cs } = useQuantLabStore.getState();
    let entries = decisionStore.getCandidateEntries(cs);
    if (runId && !decisionStore.getCandidateEntry(cs, runId)) {
      entries = [...entries, buildCandidateEntry(runId)];
    }
    await saveCandidatesStore({
      ...cs,
      entries,
      baseline_run_id: runId || null,
      updated_at: new Date().toISOString(),
    });
  }, [saveCandidatesStore]);

  const saveSweepStore = useCallback(async (nextStore) => {
    const normalized = sweepDecisionStore.normalizeSweepDecisionStore(nextStore);
    useQuantLabStore.getState().applySweepDecisionStore(normalized);
    try {
      const persisted = sweepDecisionStore.normalizeSweepDecisionStore(
        await getBridge().saveSweepDecisionStore(normalized)
      );
      useQuantLabStore.getState().applySweepDecisionStore(persisted);
    } catch (_error) {
      // Keep optimistic sweep decision state if persistence is temporarily unavailable.
    }
  }, []);

  const toggleSweepEntry = useCallback(async (row) => {
    const entryId = row?.entry_id;
    if (!entryId) return;
    const { sweepDecisionStore: sds } = useQuantLabStore.getState();
    const existing = sweepDecisionStore.getSweepDecisionEntry(sds, entryId);
    const entries = sweepDecisionStore.getSweepDecisionEntries(sds)
      .filter((e) => e.entry_id !== entryId);
    if (!existing) {
      entries.push({
        entry_id: entryId,
        sweep_run_id: row.sweep_run_id || row.sweep?.run_id || '',
        source: row.source || 'leaderboard',
        row_index: typeof row.row_index === 'number' ? row.row_index : 0,
        config_path: row.config_path || '',
        row_snapshot: row,
        shortlisted: false,
        note: '',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }
    await saveSweepStore({ ...sds, entries, updated_at: new Date().toISOString() });
  }, [saveSweepStore]);

  const toggleSweepShortlist = useCallback(async (entryId) => {
    const { sweepDecisionStore: sds } = useQuantLabStore.getState();
    const existing = sweepDecisionStore.getSweepDecisionEntry(sds, entryId);
    if (!existing) return;
    const entries = sweepDecisionStore.getSweepDecisionEntries(sds)
      .map((e) => e.entry_id === entryId
        ? { ...e, shortlisted: !e.shortlisted, updated_at: new Date().toISOString() }
        : e);
    await saveSweepStore({ ...sds, entries, updated_at: new Date().toISOString() });
  }, [saveSweepStore]);

  const setSweepBaseline = useCallback(async (entryId) => {
    const { sweepDecisionStore: sds } = useQuantLabStore.getState();
    await saveSweepStore({
      ...sds,
      baseline_entry_id: entryId || null,
      updated_at: new Date().toISOString(),
    });
  }, [saveSweepStore]);

  // ── Full refresh ───────────────────────────────────────────────────────────

  const refresh = useCallback(async (workspaceOverride = null) => {
    const workspace = workspaceOverride || await getBridge().getWorkspaceState();
    const [{ snapshot, snapshotStatus }, candidatesStoreData, sweepStore, experimentsWorkspace] =
      await Promise.all([
        loadSnapshot(workspace),
        getBridge().getCandidatesStore().then(decisionStore.normalizeCandidatesStore),
        getBridge().getSweepDecisionStore().then(sweepDecisionStore.normalizeSweepDecisionStore),
        loadExperimentsWorkspace(),
      ]);

    useQuantLabStore.getState().applyRefresh({
      workspace,
      snapshot,
      snapshotStatus,
      candidatesStore: candidatesStoreData,
      sweepDecisionStore: sweepStore,
      experimentsWorkspace,
    });
  }, []);

  useEffect(() => {
    let mounted = true;

    refresh().catch((error) => {
      if (!mounted) return;
      useQuantLabStore.getState().applyWorkspaceError(error);
    });

    const unsubscribe = getBridge().onWorkspaceState((workspace) => {
      if (!mounted) return;
      refresh(workspace).catch(() => {});
    });

    return () => {
      mounted = false;
      unsubscribe();
    };
  }, [refresh]);

  // ── Context value ──────────────────────────────────────────────────────────

  const contextState = useMemo(() => ({
    ...storeState,
    runs: getRuns(),
    launchControl: storeState.snapshot.launchControl,
    decisionStore: storeState.candidatesStore,
    decision,
    sweepDecision,
  }), [storeState, getRuns, decision, sweepDecision]);

  return useMemo(() => ({
    state: contextState,
    getRuns,
    getLatestRun,
    findRun,
    getSelectedRuns,
    getJobs,
    findJob,
    getLatestFailedJob,
    getRunRelatedJobs,
    getSweepDecisionEntriesForRun,
    findSweepDecisionRow,
    loadRunDetail,
    decision,
    openTab,
    openJobTab,
    refreshJobTab,
    closeTab,
    setActiveTab,
    toggleRunSelection,
    toggleCandidate,
    toggleShortlist,
    setBaseline,
    toggleSweepEntry,
    toggleSweepShortlist,
    setSweepBaseline,
    refresh,
  }), [
    contextState,
    getRuns,
    getLatestRun,
    findRun,
    getSelectedRuns,
    getJobs,
    findJob,
    getLatestFailedJob,
    getRunRelatedJobs,
    getSweepDecisionEntriesForRun,
    findSweepDecisionRow,
    loadRunDetail,
    decision,
    openTab,
    openJobTab,
    refreshJobTab,
    closeTab,
    setActiveTab,
    toggleRunSelection,
    toggleCandidate,
    toggleShortlist,
    setBaseline,
    toggleSweepEntry,
    toggleSweepShortlist,
    setSweepBaseline,
    refresh,
  ]);
}

export const QuantLabContextProvider = ({ value, children }) => (
  <QuantLabContext.Provider value={value}>{children}</QuantLabContext.Provider>
);
