import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Tab } from '../../shared/models/tab';
import type { WorkspaceState } from '../../shared/models/workspace';
import type { SnapshotStatus } from '../../shared/models/snapshot';

// ── Domain types ──────────────────────────────────────────────────────────────

export interface RunRecord {
  run_id: string;
  path?: string;
  [key: string]: unknown;
}

export interface JobRecord {
  request_id?: string;
  run_id?: string;
  linked_run_id?: string;
  status?: string;
  command?: string;
  summary?: string;
  stdout_href?: string;
  stderr_href?: string;
  created_at?: string;
  started_at?: string;
  payload?: Record<string, unknown>;
  request?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface SnapshotData {
  runsRegistry: { runs: RunRecord[] };
  launchControl: { jobs: JobRecord[] };
  paperHealth: unknown;
  brokerHealth: unknown;
  stepbitWorkspace: unknown;
}

export interface CandidateEntry {
  run_id: string;
  note: string;
  shortlisted: boolean;
  created_at: string;
  updated_at: string;
}

export interface CandidatesStore {
  version: number;
  updated_at: string | null;
  baseline_run_id: string | null;
  entries: CandidateEntry[];
}

export interface SweepDecisionEntry {
  entry_id: string;
  sweep_run_id: string;
  source: string;
  row_index: number;
  note: string;
  shortlisted: boolean;
  config_path: string;
  row_snapshot: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface SweepDecisionStore {
  version: number;
  updated_at: string | null;
  baseline_entry_id: string | null;
  entries: SweepDecisionEntry[];
}

export interface ExperimentsConfig {
  name: string;
  path: string;
  relativePath: string;
  modifiedAt: string;
  sizeBytes: number;
  previewText: string;
}

export interface ExperimentsSweep {
  run_id: string;
  path: string;
  mode: string;
  configPath: string;
  configName: string;
  decisionRows: unknown[];
  hasStructuredData: boolean;
}

export type ExperimentsStatus = 'idle' | 'ready' | 'error';

export interface ExperimentsWorkspace {
  status: ExperimentsStatus;
  configs: ExperimentsConfig[];
  sweeps: ExperimentsSweep[];
  error: string | null;
  updatedAt: string | null;
}

// ── Store shape ────────────────────────────────────────────────────────────────

export interface RefreshPayload {
  workspace: WorkspaceState;
  snapshot: SnapshotData;
  snapshotStatus: SnapshotStatus;
  candidatesStore: CandidatesStore;
  sweepDecisionStore: SweepDecisionStore;
  experimentsWorkspace: ExperimentsWorkspace;
}

interface QuantLabStoreState {
  workspace: WorkspaceState;
  snapshot: SnapshotData;
  snapshotStatus: SnapshotStatus;
  candidatesStore: CandidatesStore;
  sweepDecisionStore: SweepDecisionStore;
  selectedRunIds: string[];
  tabs: Tab[];
  activeTabId: string | null;
  experimentsWorkspace: ExperimentsWorkspace;
}

interface QuantLabStoreActions {
  applyRefresh: (payload: RefreshPayload) => void;
  applyWorkspaceError: (error: Error) => void;
  applyCandidatesStore: (store: CandidatesStore) => void;
  applySweepDecisionStore: (store: SweepDecisionStore) => void;
  upsertTab: (tab: Tab) => void;
  removeTab: (tabId: string) => void;
  setActiveTabId: (tabId: string | null) => void;
  toggleRunInSelection: (runId: string, max?: number) => void;
}

export type QuantLabStoreType = QuantLabStoreState & QuantLabStoreActions;

// ── Initial state ──────────────────────────────────────────────────────────────

const INITIAL_WORKSPACE: WorkspaceState = {
  status: 'starting',
  serverUrl: null,
  logs: [],
  error: null,
  source: null,
};

const INITIAL_SNAPSHOT: SnapshotData = {
  runsRegistry: { runs: [] },
  launchControl: { jobs: [] },
  paperHealth: null,
  brokerHealth: null,
  stepbitWorkspace: null,
};

const INITIAL_SNAPSHOT_STATUS: SnapshotStatus = {
  status: 'idle',
  error: null,
  source: 'none',
  lastSuccessAt: null,
  consecutiveErrors: 0,
  refreshPaused: false,
};

const INITIAL_CANDIDATES_STORE: CandidatesStore = {
  version: 1,
  updated_at: null,
  baseline_run_id: null,
  entries: [],
};

const INITIAL_SWEEP_DECISION_STORE: SweepDecisionStore = {
  version: 1,
  updated_at: null,
  baseline_entry_id: null,
  entries: [],
};

const INITIAL_EXPERIMENTS: ExperimentsWorkspace = {
  status: 'idle',
  configs: [],
  sweeps: [],
  error: null,
  updatedAt: null,
};

const INITIAL_TABS: Tab[] = [
  { id: 'runs-native', kind: 'runs', navKind: 'runs', title: 'Runs' },
];

// ── Store ──────────────────────────────────────────────────────────────────────

export const useQuantLabStore = create<QuantLabStoreType>()(
  devtools(
    (set) => ({
      workspace: INITIAL_WORKSPACE,
      snapshot: INITIAL_SNAPSHOT,
      snapshotStatus: INITIAL_SNAPSHOT_STATUS,
      candidatesStore: INITIAL_CANDIDATES_STORE,
      sweepDecisionStore: INITIAL_SWEEP_DECISION_STORE,
      selectedRunIds: [],
      tabs: INITIAL_TABS,
      activeTabId: 'runs-native',
      experimentsWorkspace: INITIAL_EXPERIMENTS,

      applyRefresh: (payload) =>
        set(
          {
            workspace: payload.workspace,
            snapshot: payload.snapshot,
            snapshotStatus: payload.snapshotStatus,
            candidatesStore: payload.candidatesStore,
            sweepDecisionStore: payload.sweepDecisionStore,
            experimentsWorkspace: payload.experimentsWorkspace,
          },
          false,
          'applyRefresh'
        ),

      applyWorkspaceError: (error) =>
        set(
          (state) => ({
            workspace: {
              ...state.workspace,
              status: 'error',
              error: error.message || String(error),
            },
            snapshotStatus: {
              status: 'degraded',
              error: error.message || String(error),
              source: 'none',
              lastSuccessAt: null,
              consecutiveErrors: 1,
              refreshPaused: false,
            },
          }),
          false,
          'applyWorkspaceError'
        ),

      applyCandidatesStore: (store) =>
        set({ candidatesStore: store }, false, 'applyCandidatesStore'),

      applySweepDecisionStore: (store) =>
        set({ sweepDecisionStore: store }, false, 'applySweepDecisionStore'),

      upsertTab: (tab) =>
        set(
          (state) => {
            const tabs = state.tabs.some((t) => t.id === tab.id)
              ? state.tabs.map((t) => (t.id === tab.id ? { ...t, ...tab } : t))
              : [...state.tabs, tab];
            return { tabs, activeTabId: tab.id };
          },
          false,
          'upsertTab'
        ),

      removeTab: (tabId) =>
        set(
          (state) => {
            const tabs = state.tabs.filter((t) => t.id !== tabId);
            const activeTabId =
              state.activeTabId === tabId
                ? (tabs[tabs.length - 1]?.id ?? null)
                : state.activeTabId;
            return { tabs, activeTabId };
          },
          false,
          'removeTab'
        ),

      setActiveTabId: (tabId) =>
        set(
          (state) => {
            if (tabId === null || state.tabs.some((t) => t.id === tabId)) {
              return { activeTabId: tabId };
            }
            return state;
          },
          false,
          'setActiveTabId'
        ),

      toggleRunInSelection: (runId, max = 4) =>
        set(
          (state) => {
            const selected = state.selectedRunIds.includes(runId);
            const selectedRunIds = selected
              ? state.selectedRunIds.filter((id) => id !== runId)
              : state.selectedRunIds.length < max
                ? [...state.selectedRunIds, runId]
                : state.selectedRunIds;
            return { selectedRunIds };
          },
          false,
          'toggleRunInSelection'
        ),
    }),
    { name: 'QuantLab' }
  )
);
