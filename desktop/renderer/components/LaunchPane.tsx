import React, { useEffect, useState } from 'react';
import type { LaunchTab } from '../../shared/models/tab';
import type { SnapshotStatus } from '../../shared/models/snapshot';
import { useSnapshot } from '../hooks/useSnapshot.js';
import { formatDateTime, formatCount, titleCase } from '../modules/utils';
import { useQuantLab as _useQuantLab } from './QuantLabContext';

// QuantLabContext is a JS file; cast to any so strict-mode TSX can consume it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const useQuantLab = _useQuantLab as () => any;

// ── Local helpers ─────────────────────────────────────────────────────────────

type Signal = { label: string; tone: string };

function launchSignal(status: string | undefined): Signal {
  const v = (status ?? '').toLowerCase();
  if (!v || v === 'none') return { label: 'Pending', tone: 'tone-warning' };
  if (v.includes('succeeded')) return { label: 'Completed', tone: 'tone-positive' };
  if (v.includes('failed')) return { label: 'Failed', tone: 'tone-negative' };
  if (v.includes('running') || v.includes('queued') || v.includes('pending')) return { label: 'In flight', tone: 'tone-warning' };
  return { label: titleCase(status ?? ''), tone: 'tone-warning' };
}

// ── Backend diagnostic classification ────────────────────────────────────────
//
// Uses live snapshot status and endpointErrors from a useSnapshot hook call
// inside LaunchPane. LaunchPane calls useSnapshot unconditionally so diagnostics
// work even when SystemPane is not mounted.
//
// Token detection: the IPC bridge throws "Local API token is not configured."
// before any network request when QUANTLAB_LOCAL_API_TOKEN is empty. This error
// propagates into endpointErrors and snapshotStatus.error — safely detectable.
//
// Direct submit blocking:
//   token_missing  → block (IPC always throws before network)
//   api_unreachable → warn only (snapshot may be stale; let user try)
//   api_degraded   → warn only (launch-control might still work)

const DEFAULT_RESEARCH_UI_SERVER_URL = 'http://127.0.0.1:8000';

type LaunchBackendState = 'online' | 'connecting' | 'token_missing' | 'api_unreachable' | 'api_degraded';

type LaunchBackendDiagnostic = {
  state: LaunchBackendState;
  label: string;
  tone: 'tone-positive' | 'tone-warning' | 'tone-negative';
  explanation: string;
  action: string | null;
  failedEndpoints: string[];
  blocksDirectSubmit: boolean;
};

function hasTokenError(endpointErrors: Record<string, string>, snapshotError: string | null | undefined): boolean {
  const needle = 'token is not configured';
  if (snapshotError?.toLowerCase().includes(needle)) return true;
  return Object.values(endpointErrors).some((msg) => msg?.toLowerCase().includes(needle));
}

function classifyLaunchBackendDiagnostic(
  snapshotStatus: Partial<SnapshotStatus>,
  endpointErrors: Record<string, string>,
  serverUrl: string | null,
): LaunchBackendDiagnostic {
  const failedEndpoints = Object.keys(endpointErrors);

  if (hasTokenError(endpointErrors, snapshotStatus.error)) {
    return {
      state: 'token_missing',
      label: 'Auth token not configured',
      tone: 'tone-negative',
      explanation: 'The local API token is missing. The desktop cannot authenticate with the backend.',
      action: 'Set QUANTLAB_LOCAL_API_TOKEN in your environment before starting the desktop.',
      failedEndpoints,
      blocksDirectSubmit: true,
    };
  }

  if (snapshotStatus.status === 'ok') {
    return {
      state: 'online',
      label: 'Backend online',
      tone: 'tone-positive',
      explanation: serverUrl ? `Connected at ${serverUrl}.` : `Connected at ${DEFAULT_RESEARCH_UI_SERVER_URL}.`,
      action: null,
      failedEndpoints: [],
      blocksDirectSubmit: false,
    };
  }

  if (snapshotStatus.status === 'degraded') {
    return {
      state: 'api_degraded',
      label: 'Backend partially available',
      tone: 'tone-warning',
      explanation: snapshotStatus.error
        ? `Some endpoints are failing: ${snapshotStatus.error}`
        : 'Some required API endpoints are not responding.',
      action: 'Check backend logs. Some features may be limited.',
      failedEndpoints,
      blocksDirectSubmit: false,
    };
  }

  if (snapshotStatus.status === 'error') {
    return {
      state: 'api_unreachable',
      label: 'Backend not running',
      tone: 'tone-negative',
      explanation: 'The research backend is not responding to API requests.',
      action: 'Start it from the repo root: python research_ui/server.py',
      failedEndpoints,
      blocksDirectSubmit: false,
    };
  }

  // idle — not yet polled or URL resolved
  return {
    state: 'connecting',
    label: 'Connecting…',
    tone: 'tone-warning',
    explanation: 'Waiting for the first backend response.',
    action: null,
    failedEndpoints: [],
    blocksDirectSubmit: false,
  };
}

// ── Guided builder contract ───────────────────────────────────────────────────
//
// Precedence rule (enforced by mergeTemplateWithOverrides):
//
//   DEFAULT_GUIDED_STATE → template fields → operator overrides → builderStateToConfig()
//
// The merge ALWAYS happens before serialization.
// builderStateToConfig() receives ONE already-merged state object.
// Preview must be generated by builderStateToConfig() only — no separate preview serialization.

type GuidedBuilderState = {
  command: 'run' | 'sweep';
  asset: string;
  quote: string;
  timeframe: string;
  periodPreset: '30d' | '90d' | '1y' | 'custom';
  startDate: string;
  endDate: string;
  validationMode: 'backtest' | 'walkforward';
  runName: string;
  notes: string;
  feesEnabled: boolean;
  slippageEnabled: boolean;
};

// Subset populated from a filesystem template. Fields here override DEFAULT_GUIDED_STATE
// but are themselves overridden by operator explicit changes.
type TemplateConfig = Partial<Omit<GuidedBuilderState, 'runName' | 'notes'>>;

// What the operator has explicitly set. Unset keys fall back via template → defaults.
type GuidedBuilderOverrides = Partial<GuidedBuilderState>;

// The single type received by builderStateToConfig() — always fully resolved.
type MergedLaunchState = GuidedBuilderState;

// The exact payload shape sent to /api/launch-control.
type LaunchConfigPayload = {
  command: 'run' | 'sweep';
  params: Record<string, string | boolean>;
};

const DEFAULT_GUIDED_STATE: GuidedBuilderState = {
  command: 'run',
  asset: 'ETH',
  quote: 'USDT',
  timeframe: '1h',
  periodPreset: '30d',
  startDate: '',
  endDate: '',
  validationMode: 'backtest',
  runName: '',
  notes: '',
  feesEnabled: true,
  slippageEnabled: true,
};

/**
 * Resolve a fully merged state from three layers in priority order:
 *   DEFAULT_GUIDED_STATE → template fields → operator overrides
 *
 * This ensures template values override defaults without being silently stomped
 * by un-touched default fields, and operator overrides always win over both.
 * The resulting MergedLaunchState is the single input to builderStateToConfig().
 */
function mergeTemplateWithOverrides(
  template: TemplateConfig,
  overrides: GuidedBuilderOverrides,
): MergedLaunchState {
  return { ...DEFAULT_GUIDED_STATE, ...template, ...overrides } as MergedLaunchState;
}

/**
 * Serialize a merged builder state into the exact payload submitted to Core.
 * This is the ONLY serialization path — used for preview (and, in a future slice, submit).
 * Do not call with un-merged state.
 */
function builderStateToConfig(merged: MergedLaunchState): LaunchConfigPayload {
  const params: Record<string, string | boolean> = {
    asset: merged.asset,
    quote: merged.quote,
    timeframe: merged.timeframe,
    validation_mode: merged.validationMode,
    fees_enabled: merged.feesEnabled,
    slippage_enabled: merged.slippageEnabled,
  };

  if (merged.periodPreset === 'custom') {
    if (merged.startDate) params.start_date = merged.startDate;
    if (merged.endDate) params.end_date = merged.endDate;
  } else {
    params.period_preset = merged.periodPreset;
  }

  if (merged.runName.trim()) params.run_name = merged.runName.trim();
  if (merged.notes.trim()) params.notes = merged.notes.trim();

  return { command: merged.command, params };
}

function isGuidedStateValid(state: MergedLaunchState): boolean {
  if (!state.asset.trim() || !state.quote.trim() || !state.timeframe.trim()) return false;
  if (state.periodPreset === 'custom' && !state.startDate && !state.endDate) return false;
  return true;
}

// ── Conservative YAML template extractor ─────────────────────────────────────
//
// Extracts only well-known structural signals from raw YAML text using simple
// line-level regex. Does not implement a full YAML parser. Fields not present
// or not safely derivable are omitted — defaults fill the gap.
//
// Extracted signals:
//   ticker: "ETH-USD" → asset + quote (split on "-")
//   interval: "1d"    → timeframe
//   start/end: ISO    → periodPreset='custom' + startDate/endDate
//   fee: 0.002        → feesEnabled (true if > 0)
//   slippage_bps: 8.0 → slippageEnabled (true if > 0)
//   param_grid:       → command='sweep'
//   splits:           → validationMode='walkforward'

function extractTemplateFromYaml(text: string): TemplateConfig {
  const template: TemplateConfig = {};

  const tickerMatch = text.match(/^ticker:\s*["']?([A-Z]+-[A-Z]+)["']?\s*$/m);
  if (tickerMatch) {
    const parts = tickerMatch[1].split('-');
    if (parts.length === 2) {
      template.asset = parts[0];
      template.quote = parts[1];
    }
  }

  const intervalMatch = text.match(/^interval:\s*["']?(\w+)["']?\s*$/m);
  if (intervalMatch) {
    template.timeframe = intervalMatch[1];
  }

  const startMatch = text.match(/^start:\s*["']?(\d{4}-\d{2}-\d{2})["']?\s*$/m);
  const endMatch   = text.match(/^end:\s*["']?(\d{4}-\d{2}-\d{2})["']?\s*$/m);
  if (startMatch || endMatch) {
    template.periodPreset = 'custom';
    if (startMatch) template.startDate = startMatch[1];
    if (endMatch)   template.endDate   = endMatch[1];
  }

  const feeMatch = text.match(/^fee:\s*([\d.]+)\s*$/m);
  if (feeMatch) template.feesEnabled = parseFloat(feeMatch[1]) > 0;

  const slippageMatch = text.match(/^slippage_bps:\s*([\d.]+)\s*$/m);
  if (slippageMatch) template.slippageEnabled = parseFloat(slippageMatch[1]) > 0;

  if (/^param_grid:/m.test(text)) template.command = 'sweep';
  if (/^splits:/m.test(text))     template.validationMode = 'walkforward';

  return template;
}

// ── Shared config file loading hook ──────────────────────────────────────────

const EXPERIMENTS_CONFIG_DIR = 'configs/experiments';
const CUSTOM_CONFIG_VALUE = '__custom__';

type ConfigOption = { name: string; path: string };
type ConfigLoadStatus = 'loading' | 'ready' | 'empty';

function useConfigOptions(): { options: ConfigOption[]; status: ConfigLoadStatus } {
  const [options, setOptions] = useState<ConfigOption[]>([]);
  const [status, setStatus] = useState<ConfigLoadStatus>('loading');

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const listing = await window.quantlabDesktop.listDirectory(EXPERIMENTS_CONFIG_DIR, 1);
        const loaded = (listing.entries || [])
          .filter((e: any) => e.kind === 'file' && /\.(ya?ml|json)$/i.test(e.name || ''))
          .map((e: any) => ({ name: e.relative_path || e.name, path: e.relative_path || e.path || e.name }))
          .sort((a: ConfigOption, b: ConfigOption) => a.path.localeCompare(b.path));
        if (cancelled) return;
        setOptions(loaded);
        setStatus(loaded.length ? 'ready' : 'empty');
      } catch {
        if (cancelled) return;
        setOptions([]);
        setStatus('empty');
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  return { options, status };
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SummaryCard({ label, value, tone = '' }: { label: string; value: string; tone?: string }) {
  return (
    <article className={`summary-card ${tone}`}>
      <div className="label">{label}</div>
      <div className={`value ${tone}`}>{value}</div>
    </article>
  );
}

function JobCard({ job, onOpen }: { job: any; onOpen: () => void }) {
  const sig = launchSignal(job.status);
  return (
    <button className="system-job-item" type="button" onClick={onOpen}>
      <div className="system-job-top">
        <strong>{titleCase(job.command ?? 'unknown')}</strong>
        <span className={sig.tone}>{sig.label}</span>
      </div>
      <div className="artifact-meta">
        {job.request_id ?? '-'}{job.run_id ? ` · ${job.run_id}` : ''}
      </div>
      <div className="artifact-meta">
        {job.summary ?? 'No summary'} · {formatDateTime(job.created_at ?? job.started_at)}
      </div>
    </button>
  );
}

function FilePreview({ content, error, loading }: { content: string | null; error: string | null; loading: boolean }) {
  if (loading) return <div className="artifact-meta">Loading file…</div>;
  if (error)   return <div className="artifact-meta" style={{ color: 'var(--danger)' }}>{error}</div>;
  if (!content) return null;
  return (
    <pre className="artifact-meta" style={{
      background: 'var(--bg-soft)',
      border: '1px solid var(--border)',
      borderRadius: '6px',
      padding: '10px 12px',
      fontSize: '11px',
      lineHeight: '1.6',
      overflowX: 'auto',
      margin: '0',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-all',
    }}>
      {content}
    </pre>
  );
}

// ── Backend diagnostic panel ──────────────────────────────────────────────────

function BackendDiagnosticPanel({ diagnostic }: { diagnostic: LaunchBackendDiagnostic }) {
  return (
    <div className={`ops-callout ${diagnostic.tone}`} style={{ marginBottom: '12px' }}>
      <strong>{diagnostic.label}</strong>
      {' — '}{diagnostic.explanation}
      {diagnostic.action && (
        <div className="artifact-meta" style={{ marginTop: '4px' }}>
          {diagnostic.action}
        </div>
      )}
      {diagnostic.failedEndpoints.length > 0 && (
        <div className="artifact-meta" style={{ marginTop: '4px' }}>
          Failed endpoints: {diagnostic.failedEndpoints.join(', ')}
        </div>
      )}
    </div>
  );
}

// ── Guided builder tab ────────────────────────────────────────────────────────

function GuidedBuilderTab({ configOptions, configLoadStatus, diagnostic }: {
  configOptions: ConfigOption[];
  configLoadStatus: ConfigLoadStatus;
  diagnostic: LaunchBackendDiagnostic;
}) {
  // Tracks only what the operator has explicitly changed.
  const [overrides, setOverrides] = useState<GuidedBuilderOverrides>({});

  // Template state — populated from filesystem when operator selects a base config.
  const [selectedTemplatePath, setSelectedTemplatePath] = useState<string>(CUSTOM_CONFIG_VALUE);
  const [template, setTemplate] = useState<TemplateConfig>({});
  const [templateLoadStatus, setTemplateLoadStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [showPreview, setShowPreview] = useState(false);

  // Load and extract template fields when a config is selected as base.
  useEffect(() => {
    if (selectedTemplatePath === CUSTOM_CONFIG_VALUE) {
      setTemplate({});
      setTemplateLoadStatus('idle');
      return;
    }
    let cancelled = false;
    setTemplateLoadStatus('loading');
    window.quantlabDesktop.readProjectText(selectedTemplatePath)
      .then((text: string) => {
        if (cancelled) return;
        setTemplate(extractTemplateFromYaml(text));
        setTemplateLoadStatus('ready');
      })
      .catch(() => {
        if (cancelled) return;
        setTemplate({});
        setTemplateLoadStatus('error');
      });
    return () => { cancelled = true; };
  }, [selectedTemplatePath]);

  // Resolved display values — form fields read from here, not from overrides directly.
  const mergedState = mergeTemplateWithOverrides(template, overrides);
  // builderStateToConfig() is the single serialization path for both preview and (future) submit.
  const payload = builderStateToConfig(mergedState);
  const previewText = JSON.stringify(payload, null, 2);
  const valid = isGuidedStateValid(mergedState);

  function set<K extends keyof GuidedBuilderState>(key: K, value: GuidedBuilderState[K]) {
    setOverrides((prev) => ({ ...prev, [key]: value }));
  }

  const templateFields = Object.keys(template);

  return (
    <section className="artifact-panel">
      <div className="section-label">Guided</div>

      <BackendDiagnosticPanel diagnostic={diagnostic} />

      <form className="launch-form" onSubmit={(e) => e.preventDefault()}>

        {/* Template base selector */}
        <div className="launch-form-row">
          <label className="launch-label" htmlFor="guided-template-select">Base config</label>
          <div>
            {configLoadStatus === 'loading' ? (
              <div className="launch-hint">Reading configs/experiments/…</div>
            ) : configOptions.length ? (
              <select
                id="guided-template-select"
                className="launch-input"
                value={selectedTemplatePath}
                onChange={(e) => {
                  setSelectedTemplatePath(e.target.value);
                  // Reset overrides when switching templates so operator sees clean template defaults.
                  setOverrides({});
                }}
              >
                <option value={CUSTOM_CONFIG_VALUE}>No template — use defaults</option>
                {configOptions.map((o) => (
                  <option key={o.path} value={o.path}>{o.path}</option>
                ))}
              </select>
            ) : (
              <div className="launch-hint">No config files found in configs/experiments.</div>
            )}
            {templateLoadStatus === 'loading' && <div className="launch-hint">Reading template…</div>}
            {templateLoadStatus === 'error' && (
              <div className="launch-hint" style={{ color: 'var(--danger)' }}>Could not read template file.</div>
            )}
            {templateLoadStatus === 'ready' && templateFields.length > 0 && (
              <div className="launch-hint">Applied: {templateFields.join(', ')}</div>
            )}
            {templateLoadStatus === 'ready' && templateFields.length === 0 && (
              <div className="launch-hint">No extractable fields — defaults apply.</div>
            )}
          </div>
        </div>

        {/* Mode */}
        <div className="launch-form-row">
          <label className="launch-label">Mode</label>
          <div className="workflow-actions">
            {(['run', 'sweep'] as const).map((cmd) => (
              <button
                key={cmd}
                type="button"
                className={`ghost-btn ${mergedState.command === cmd ? 'is-selected' : ''}`}
                onClick={() => set('command', cmd)}
              >
                {cmd === 'run' ? 'Run' : 'Sweep'}
              </button>
            ))}
          </div>
        </div>

        {/* Market (asset + quote on one row) */}
        <div className="launch-form-row">
          <label className="launch-label" htmlFor="guided-asset">Market</label>
          <div className="launch-market-pair">
            <input
              id="guided-asset"
              className="launch-input"
              type="text"
              placeholder="ETH"
              value={mergedState.asset}
              onChange={(e) => set('asset', e.target.value.toUpperCase())}
            />
            <input
              id="guided-quote"
              className="launch-input"
              type="text"
              placeholder="USDT"
              value={mergedState.quote}
              onChange={(e) => set('quote', e.target.value.toUpperCase())}
            />
          </div>
        </div>

        {/* Timeframe */}
        <div className="launch-form-row">
          <label className="launch-label">Timeframe</label>
          <div className="workflow-actions">
            {['1h', '4h', '1d'].map((tf) => (
              <button
                key={tf}
                type="button"
                className={`ghost-btn ${mergedState.timeframe === tf ? 'is-selected' : ''}`}
                onClick={() => set('timeframe', tf)}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Period */}
        <div className="launch-form-row">
          <label className="launch-label">Period</label>
          <div>
            <div className="workflow-actions">
              {(['30d', '90d', '1y', 'custom'] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  className={`ghost-btn ${mergedState.periodPreset === p ? 'is-selected' : ''}`}
                  onClick={() => set('periodPreset', p)}
                >
                  {p}
                </button>
              ))}
            </div>
            {mergedState.periodPreset === 'custom' && (
              <div className="launch-date-pair">
                <input
                  className="launch-input"
                  type="date"
                  value={mergedState.startDate}
                  onChange={(e) => set('startDate', e.target.value)}
                />
                <input
                  className="launch-input"
                  type="date"
                  value={mergedState.endDate}
                  onChange={(e) => set('endDate', e.target.value)}
                />
              </div>
            )}
          </div>
        </div>

        {/* Validation */}
        <div className="launch-form-row">
          <label className="launch-label">Validation</label>
          <div className="workflow-actions">
            {(['backtest', 'walkforward'] as const).map((m) => (
              <button
                key={m}
                type="button"
                className={`ghost-btn ${mergedState.validationMode === m ? 'is-selected' : ''}`}
                onClick={() => set('validationMode', m)}
              >
                {m === 'backtest' ? 'Backtest' : 'Walk-forward'}
              </button>
            ))}
          </div>
        </div>

        {/* Costs */}
        <div className="launch-form-row">
          <label className="launch-label">Costs</label>
          <div className="workflow-actions">
            <button
              type="button"
              className={`ghost-btn ${mergedState.feesEnabled ? 'is-selected' : ''}`}
              onClick={() => set('feesEnabled', !mergedState.feesEnabled)}
            >
              {mergedState.feesEnabled ? 'Fees on' : 'Fees off'}
            </button>
            <button
              type="button"
              className={`ghost-btn ${mergedState.slippageEnabled ? 'is-selected' : ''}`}
              onClick={() => set('slippageEnabled', !mergedState.slippageEnabled)}
            >
              {mergedState.slippageEnabled ? 'Slippage on' : 'Slippage off'}
            </button>
          </div>
        </div>

        {/* Run name */}
        <div className="launch-form-row">
          <label className="launch-label" htmlFor="guided-run-name">Run name</label>
          <input
            id="guided-run-name"
            className="launch-input"
            type="text"
            placeholder="Optional…"
            value={mergedState.runName}
            onChange={(e) => set('runName', e.target.value)}
          />
        </div>

        {/* Notes */}
        <div className="launch-form-row">
          <label className="launch-label" htmlFor="guided-notes">Notes</label>
          <input
            id="guided-notes"
            className="launch-input"
            type="text"
            placeholder="Optional"
            value={mergedState.notes}
            onChange={(e) => set('notes', e.target.value)}
          />
        </div>

        {/* Payload preview — generated by builderStateToConfig(), same path used for submit */}
        <div className="launch-form-row no-border">
          <label className="launch-label" style={{ paddingTop: '5px' }}>Preview</label>
          <div>
            <button
              type="button"
              className="ghost-btn mini"
              onClick={() => setShowPreview((v) => !v)}
            >
              {showPreview ? 'Hide' : 'Show'}
            </button>
            {showPreview && (
              <pre className="artifact-meta" style={{
                background: 'var(--bg-soft)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                padding: '10px 12px',
                fontSize: '11px',
                lineHeight: '1.6',
                overflowX: 'auto',
                margin: '6px 0 0',
              }}>
                {previewText}
              </pre>
            )}
            {!valid && (
              <div className="launch-hint" style={{ marginTop: '4px' }}>
                Asset, quote, and timeframe required. Custom period needs at least one date.
              </div>
            )}
          </div>
        </div>

        {/* Submit disabled — enabled in a follow-up slice after submit contract is finalized */}
        <div className="ops-callout tone-warning" style={{ marginTop: '10px' }}>
          Guided submit is not active in this slice. Use <strong>Direct YAML</strong> to submit jobs now.
          Guided submit will be enabled after the submit contract is finalized.
        </div>
      </form>
    </section>
  );
}

// ── Direct YAML tab ───────────────────────────────────────────────────────────

function DirectYamlTab({ onRefresh, configOptions, configLoadStatus, diagnostic }: {
  onRefresh: () => void;
  configOptions: ConfigOption[];
  configLoadStatus: ConfigLoadStatus;
  diagnostic: LaunchBackendDiagnostic;
}) {
  const [command, setCommand] = useState<'run' | 'sweep'>('sweep');
  const [configPath, setConfigPath] = useState('');
  const [configSelection, setConfigSelection] = useState(CUSTOM_CONFIG_VALUE);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // File preview state — populated via readProjectText when a file is selected.
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  // Seed first config when options arrive.
  useEffect(() => {
    if (configOptions.length && configPath === '' && configSelection === CUSTOM_CONFIG_VALUE) {
      setConfigSelection(configOptions[0].path);
      setConfigPath(configOptions[0].path);
    }
  }, [configOptions]);

  // Read file content whenever selection changes to a real path.
  useEffect(() => {
    if (configSelection === CUSTOM_CONFIG_VALUE || !configSelection) {
      setPreviewContent(null);
      setPreviewError(null);
      return;
    }
    let cancelled = false;
    setPreviewLoading(true);
    setPreviewContent(null);
    setPreviewError(null);
    window.quantlabDesktop.readProjectText(configSelection)
      .then((text: string) => {
        if (cancelled) return;
        setPreviewContent(text || '(empty file)');
        setPreviewLoading(false);
      })
      .catch((err: any) => {
        if (cancelled) return;
        setPreviewError(`Could not read file: ${err?.message ?? configSelection}`);
        setPreviewLoading(false);
      });
    return () => { cancelled = true; };
  }, [configSelection]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setStatus('Submitting…');
    try {
      const params: Record<string, string> = {};
      if (command === 'sweep' && configPath.trim()) params.config_path = configPath.trim();
      const result = await window.quantlabDesktop.postJson('/api/launch-control', { command, params }) as any;
      setStatus(result?.message ?? 'Launch accepted.');
      setConfigPath('');
      await onRefresh();
    } catch (err: any) {
      setStatus(`Error: ${err?.message ?? 'Launch failed.'}`);
    } finally {
      setBusy(false);
    }
  };

  const hasPreviewable = configSelection !== CUSTOM_CONFIG_VALUE && configSelection;
  const submitBlocked = busy || diagnostic.blocksDirectSubmit || (command === 'sweep' && !configPath.trim());

  return (
    <section className="artifact-panel">
      <div className="section-label">Direct YAML</div>
      <h3>Submit from config file</h3>
      <p className="artifact-meta" style={{ marginBottom: '14px' }}>
        Select or enter an existing config path and submit directly.
      </p>
      <BackendDiagnosticPanel diagnostic={diagnostic} />
      <form className="launch-form" onSubmit={handleSubmit}>
        <div className="launch-form-row">
          <label className="launch-label">Command</label>
          <div className="workflow-actions">
            <button
              type="button"
              className={`ghost-btn ${command === 'run' ? 'is-selected' : ''}`}
              onClick={() => setCommand('run')}
            >
              Run
            </button>
            <button
              type="button"
              className={`ghost-btn ${command === 'sweep' ? 'is-selected' : ''}`}
              onClick={() => setCommand('sweep')}
            >
              Sweep
            </button>
          </div>
        </div>
        {command === 'sweep' && (
          <div className="launch-form-row">
            <label className="launch-label" htmlFor={configOptions.length ? 'launch-config-select' : 'launch-config-path'}>
              Config path
            </label>
            {configOptions.length ? (
              <select
                id="launch-config-select"
                className="launch-input"
                value={configSelection}
                onChange={(e) => {
                  const next = e.target.value;
                  setConfigSelection(next);
                  setConfigPath(next === CUSTOM_CONFIG_VALUE ? '' : next);
                }}
                disabled={busy}
              >
                {configOptions.map((o) => (
                  <option key={o.path} value={o.path}>{o.path}</option>
                ))}
                <option value={CUSTOM_CONFIG_VALUE}>Custom path…</option>
              </select>
            ) : (
              <div className="artifact-meta">
                {configLoadStatus === 'loading'
                  ? 'Reading configs/experiments/...'
                  : 'No config files found in configs/experiments.'}
              </div>
            )}
            {(!configOptions.length || configSelection === CUSTOM_CONFIG_VALUE) && (
              <input
                id="launch-config-path"
                className="launch-input"
                type="text"
                placeholder="configs/experiments/my_config.yaml"
                value={configPath}
                onChange={(e) => setConfigPath(e.target.value)}
                disabled={busy}
              />
            )}

            {/* File preview */}
            {hasPreviewable && (
              <div style={{ marginTop: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span className="launch-label">File preview</span>
                  <button
                    type="button"
                    className="ghost-btn mini"
                    onClick={() => setShowPreview((v) => !v)}
                  >
                    {showPreview ? 'Hide' : 'Show'}
                  </button>
                </div>
                {showPreview && (
                  <FilePreview
                    content={previewContent}
                    error={previewError}
                    loading={previewLoading}
                  />
                )}
              </div>
            )}
          </div>
        )}
        <div className="workflow-actions" style={{ marginTop: '12px' }}>
          <button
            className="ghost-btn"
            type="submit"
            disabled={submitBlocked}
            title={diagnostic.blocksDirectSubmit ? diagnostic.action ?? diagnostic.label : undefined}
          >
            {busy ? 'Submitting…' : 'Submit'}
          </button>
        </div>
        {diagnostic.blocksDirectSubmit && (
          <div className="artifact-meta" style={{ marginTop: '6px' }}>
            Submit blocked: {diagnostic.label.toLowerCase()}.
          </div>
        )}
        {status && <div className={`ops-callout ${status.startsWith('Error') ? 'tone-negative' : 'tone-positive'}`} style={{ marginTop: '10px' }}>{status}</div>}
      </form>
    </section>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

type LaunchBuilderTab = 'guided' | 'direct-yaml';

export function LaunchPane({ tab: _tab }: { tab: LaunchTab }) {
  const ctx = useQuantLab();
  const { state, getJobs, getLatestRun, getLatestFailedJob, openTab, refreshRegistry } = ctx;

  const snapshot = state.snapshot ?? {};
  const launchControl = (snapshot as any).launchControl ?? null;
  const serverUrl: string | null = state.workspace?.serverUrl ?? null;

  // Backend diagnostics — unconditional useSnapshot call so Launch has live
  // connectivity state even when SystemPane is not mounted.
  const workspace = state.workspace ?? {};
  const workspaceServerUrl = typeof workspace.serverUrl === 'string' ? workspace.serverUrl.trim() : '';
  const researchUiServerUrl = workspaceServerUrl || DEFAULT_RESEARCH_UI_SERVER_URL;
  const nativeDiag = useSnapshot(researchUiServerUrl);
  // useSnapshot is a JS hook — cast to avoid string/SnapshotStatusValue mismatch.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const diagSnapshotStatus: Partial<SnapshotStatus> = (nativeDiag.snapshotStatus ?? {}) as any;
  const diagEndpointErrors: Record<string, string> = nativeDiag.endpointErrors ?? {};
  const diagnostic = classifyLaunchBackendDiagnostic(diagSnapshotStatus, diagEndpointErrors, serverUrl);

  const allJobs: any[] = getJobs();
  const recentJobs: any[] = allJobs.slice(0, 10);
  const latestRun = getLatestRun();
  const latestFailedJob = getLatestFailedJob();
  const totalJobs: number = Array.isArray(launchControl?.jobs) ? launchControl.jobs.length : 0;
  const failedCount = allJobs.filter((j: any) => (j.status ?? '').toLowerCase().includes('failed')).length;
  const inFlightCount = allJobs.filter((j: any) => {
    const s = (j.status ?? '').toLowerCase();
    return s.includes('running') || s.includes('queued') || s.includes('pending');
  }).length;

  const [activeBuilderTab, setActiveBuilderTab] = useState<LaunchBuilderTab>('guided');

  // Shared config file discovery — lifted so both tabs share the same result.
  const { options: configOptions, status: configLoadStatus } = useConfigOptions();

  const openExternal = (path: string) => {
    const base = serverUrl ? serverUrl.replace(/\/$/, '') : '';
    if (typeof window.quantlabDesktop?.openExternal === 'function') {
      window.quantlabDesktop.openExternal(`${base}${path}`);
    }
  };

  return (
    <div className="tab-shell launch-pane">
      {/* Header */}
      <div className="artifact-top">
        <div>
          <div className="section-label">Launch control</div>
          <h3>Launch</h3>
          <div className="artifact-meta">
            Primary launch surface for run and sweep execution, queue review, and job log inspection.
            Browser runtime remains available only as a secondary bridge.
          </div>
        </div>
        <div className="artifact-actions">
          {serverUrl && (
            <button className="ghost-btn" type="button" onClick={() => openExternal('/research_ui/index.html#/launch')}>
              Open browser bridge
            </button>
          )}
          {latestRun?.run_id && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'run', runId: latestRun.run_id })}>
              Latest run
            </button>
          )}
          {recentJobs[0]?.request_id && (
            <button className="ghost-btn" type="button" onClick={() => openTab({ kind: 'job', requestId: recentJobs[0].request_id })}>
              Latest job
            </button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="tab-summary-grid">
        <SummaryCard label="Total jobs"   value={formatCount(totalJobs)}    tone={totalJobs ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="In flight"    value={formatCount(inFlightCount)} tone={inFlightCount ? 'tone-warning' : ''} />
        <SummaryCard label="Failed"       value={formatCount(failedCount)}   tone={failedCount ? 'tone-negative' : 'tone-positive'} />
        <SummaryCard label="Latest run"   value={latestRun?.run_id ?? 'None'} tone={latestRun?.run_id ? 'tone-positive' : 'tone-warning'} />
        <SummaryCard label="Browser bridge" value={serverUrl ? 'Available' : 'Unavailable'} tone={serverUrl ? 'tone-positive' : 'tone-warning'} />
      </div>

      {/* Failed job callout */}
      {latestFailedJob && (
        <div className="ops-callout tone-warning" style={{ marginBottom: '16px' }}>
          Latest failed job: <strong>{latestFailedJob.request_id ?? '-'}</strong>
          {' · '}{titleCase(latestFailedJob.command ?? 'unknown')}
          <button
            className="ghost-btn mini"
            type="button"
            style={{ marginLeft: '12px' }}
            onClick={() => openTab({ kind: 'job', requestId: latestFailedJob.request_id })}
          >
            Review
          </button>
        </div>
      )}

      {/* Launch queue + builder */}
      <div className="artifact-grid">
        <section className="artifact-panel">
          <div className="section-label">Launch queue</div>
          <h3>Recent jobs</h3>
          {recentJobs.length ? (
            <div className="system-job-list">
              {recentJobs.map((job: any) => (
                <JobCard
                  key={job.request_id}
                  job={job}
                  onOpen={() => openTab({ kind: 'job', requestId: job.request_id })}
                />
              ))}
            </div>
          ) : (
            <div className="empty-state">
              No launch jobs are visible yet. Submit a run or sweep to get started.
            </div>
          )}
        </section>

        {/* Builder panel with Guided / Direct YAML tabs */}
        <div>
          <div className="tab-pills" style={{ marginBottom: '12px' }}>
            <button
              className={`tab-pill ${activeBuilderTab === 'guided' ? 'is-active' : ''}`}
              type="button"
              onClick={() => setActiveBuilderTab('guided')}
            >
              Guided
            </button>
            <button
              className={`tab-pill ${activeBuilderTab === 'direct-yaml' ? 'is-active' : ''}`}
              type="button"
              onClick={() => setActiveBuilderTab('direct-yaml')}
            >
              Direct YAML
            </button>
          </div>

          {activeBuilderTab === 'guided' && (
            <GuidedBuilderTab
              configOptions={configOptions}
              configLoadStatus={configLoadStatus}
              diagnostic={diagnostic}
            />
          )}
          {activeBuilderTab === 'direct-yaml' && (
            <DirectYamlTab
              onRefresh={refreshRegistry}
              configOptions={configOptions}
              configLoadStatus={configLoadStatus}
              diagnostic={diagnostic}
            />
          )}
        </div>
      </div>
    </div>
  );
}
