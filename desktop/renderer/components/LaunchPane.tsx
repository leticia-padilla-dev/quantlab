import React, { useEffect, useState } from 'react';
import type { LaunchTab } from '../../shared/models/tab';
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

// ── Guided builder contract ───────────────────────────────────────────────────
//
// Precedence rule (enforced by mergeTemplateWithOverrides):
//
//   template fields → operator overrides → merged state → builderStateToConfig()
//
// The merge ALWAYS happens before serialization.
// builderStateToConfig() receives ONE already-merged state object.
// Preview and submit BOTH call builderStateToConfig() on the same merged state.

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

// Subset populated from a filesystem template (#567). Empty in this slice.
type TemplateConfig = Partial<Omit<GuidedBuilderState, 'runName' | 'notes'>>;

// The single type received by builderStateToConfig().
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
 * Apply template defaults first, then operator overrides on top.
 * The resulting MergedLaunchState is the single input to builderStateToConfig().
 */
function mergeTemplateWithOverrides(
  template: TemplateConfig,
  overrides: GuidedBuilderState,
): MergedLaunchState {
  return { ...template, ...overrides } as MergedLaunchState;
}

/**
 * Serialize a merged builder state into the exact payload submitted to Core.
 * This is the ONLY serialization path — used for both preview and submit.
 * Do not call with un-merged (template + overrides) state.
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

function isGuidedStateValid(state: GuidedBuilderState): boolean {
  if (!state.asset.trim() || !state.quote.trim() || !state.timeframe.trim()) return false;
  if (state.periodPreset === 'custom' && !state.startDate && !state.endDate) return false;
  return true;
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

// ── Guided builder tab ────────────────────────────────────────────────────────

// No filesystem template yet — that is wired in #567.
const CURRENT_TEMPLATE: TemplateConfig = {};

function GuidedBuilderTab({ serverUrl, onRefresh }: { serverUrl: string | null; onRefresh: () => void }) {
  const [builderState, setBuilderState] = useState<GuidedBuilderState>(DEFAULT_GUIDED_STATE);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  // Merge and serialize — both preview and submit use this path.
  const mergedState = mergeTemplateWithOverrides(CURRENT_TEMPLATE, builderState);
  const payload = builderStateToConfig(mergedState);
  const previewText = JSON.stringify(payload, null, 2);
  const valid = isGuidedStateValid(builderState);

  function set<K extends keyof GuidedBuilderState>(key: K, value: GuidedBuilderState[K]) {
    setBuilderState((prev) => ({ ...prev, [key]: value }));
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy || !valid) return;
    setBusy(true);
    setStatus('Submitting…');
    try {
      const result = await window.quantlabDesktop.postJson('/api/launch-control', payload) as any;
      setStatus(result?.message ?? 'Launch accepted.');
      await onRefresh();
    } catch (err: any) {
      setStatus(`Error: ${err?.message ?? 'Launch failed.'}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="artifact-panel">
      <div className="section-label">Guided</div>
      <h3>Build a research run</h3>
      <p className="artifact-meta" style={{ marginBottom: '14px' }}>
        Configure a run from fields. Desktop generates the exact payload sent to QuantLab Core —
        preview it before submitting. Config templates from the filesystem are added in a follow-up slice.
      </p>
      <div className={`ops-callout ${serverUrl ? 'tone-positive' : 'tone-warning'}`} style={{ marginBottom: '12px' }}>
        {serverUrl ? 'Backend: Online — ready to submit' : 'Backend: Offline — submit may be unavailable'}
      </div>

      <form className="launch-form" onSubmit={handleSubmit}>
        {/* Command */}
        <div className="launch-form-row">
          <label className="launch-label">Mode</label>
          <div className="workflow-actions">
            {(['run', 'sweep'] as const).map((cmd) => (
              <button
                key={cmd}
                type="button"
                className={`ghost-btn ${builderState.command === cmd ? 'is-selected' : ''}`}
                onClick={() => set('command', cmd)}
                disabled={busy}
              >
                {cmd === 'run' ? 'Run' : 'Sweep'}
              </button>
            ))}
          </div>
          <div className="artifact-meta" style={{ marginTop: '4px' }}>
            {builderState.command === 'run'
              ? 'Execute a single configuration once.'
              : 'Execute a parameter grid to compare combinations.'}
          </div>
        </div>

        {/* Asset / quote */}
        <div className="launch-form-row">
          <label className="launch-label" htmlFor="guided-asset">Asset</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              id="guided-asset"
              className="launch-input"
              type="text"
              placeholder="ETH"
              value={builderState.asset}
              onChange={(e) => set('asset', e.target.value.toUpperCase())}
              disabled={busy}
              style={{ flex: '1' }}
            />
            <input
              id="guided-quote"
              className="launch-input"
              type="text"
              placeholder="USDT"
              value={builderState.quote}
              onChange={(e) => set('quote', e.target.value.toUpperCase())}
              disabled={busy}
              style={{ flex: '1' }}
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
                className={`ghost-btn ${builderState.timeframe === tf ? 'is-selected' : ''}`}
                onClick={() => set('timeframe', tf)}
                disabled={busy}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Period */}
        <div className="launch-form-row">
          <label className="launch-label">Period</label>
          <div className="workflow-actions">
            {(['30d', '90d', '1y', 'custom'] as const).map((p) => (
              <button
                key={p}
                type="button"
                className={`ghost-btn ${builderState.periodPreset === p ? 'is-selected' : ''}`}
                onClick={() => set('periodPreset', p)}
                disabled={busy}
              >
                {p}
              </button>
            ))}
          </div>
          {builderState.periodPreset === 'custom' && (
            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
              <input
                className="launch-input"
                type="date"
                placeholder="Start"
                value={builderState.startDate}
                onChange={(e) => set('startDate', e.target.value)}
                disabled={busy}
                style={{ flex: '1' }}
              />
              <input
                className="launch-input"
                type="date"
                placeholder="End"
                value={builderState.endDate}
                onChange={(e) => set('endDate', e.target.value)}
                disabled={busy}
                style={{ flex: '1' }}
              />
            </div>
          )}
        </div>

        {/* Validation mode */}
        <div className="launch-form-row">
          <label className="launch-label">Validation</label>
          <div className="workflow-actions">
            {(['backtest', 'walkforward'] as const).map((m) => (
              <button
                key={m}
                type="button"
                className={`ghost-btn ${builderState.validationMode === m ? 'is-selected' : ''}`}
                onClick={() => set('validationMode', m)}
                disabled={busy}
              >
                {m === 'backtest' ? 'Backtest' : 'Walk-forward'}
              </button>
            ))}
          </div>
          <div className="artifact-meta" style={{ marginTop: '4px' }}>
            {builderState.validationMode === 'walkforward'
              ? 'Evaluates temporal robustness by dividing history into rolling windows.'
              : 'Single in-sample evaluation over the full selected period.'}
          </div>
        </div>

        {/* Costs */}
        <div className="launch-form-row">
          <label className="launch-label">Costs</label>
          <div className="workflow-actions">
            <button
              type="button"
              className={`ghost-btn ${builderState.feesEnabled ? 'is-selected' : ''}`}
              onClick={() => set('feesEnabled', !builderState.feesEnabled)}
              disabled={busy}
            >
              {builderState.feesEnabled ? 'Fees on' : 'Fees off'}
            </button>
            <button
              type="button"
              className={`ghost-btn ${builderState.slippageEnabled ? 'is-selected' : ''}`}
              onClick={() => set('slippageEnabled', !builderState.slippageEnabled)}
              disabled={busy}
            >
              {builderState.slippageEnabled ? 'Slippage on' : 'Slippage off'}
            </button>
          </div>
        </div>

        {/* Run name / notes */}
        <div className="launch-form-row">
          <label className="launch-label" htmlFor="guided-run-name">Run name</label>
          <input
            id="guided-run-name"
            className="launch-input"
            type="text"
            placeholder="Optional — defaults to generated ID"
            value={builderState.runName}
            onChange={(e) => set('runName', e.target.value)}
            disabled={busy}
          />
        </div>
        <div className="launch-form-row">
          <label className="launch-label" htmlFor="guided-notes">Notes</label>
          <input
            id="guided-notes"
            className="launch-input"
            type="text"
            placeholder="Optional"
            value={builderState.notes}
            onChange={(e) => set('notes', e.target.value)}
            disabled={busy}
          />
        </div>

        {/* Preview — generated by the same builderStateToConfig() used for submit */}
        <div className="launch-form-row">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span className="launch-label">Payload preview</span>
            <button
              type="button"
              className="ghost-btn mini"
              onClick={() => setShowPreview((v) => !v)}
            >
              {showPreview ? 'Hide' : 'Show'}
            </button>
          </div>
          {showPreview && (
            <pre className="artifact-meta" style={{
              background: 'var(--bg-soft)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '10px 12px',
              fontSize: '11px',
              lineHeight: '1.6',
              overflowX: 'auto',
              margin: '0',
            }}>
              {previewText}
            </pre>
          )}
          <div className="artifact-meta" style={{ marginTop: '4px' }}>
            Preview and submit use the same serialization path.
          </div>
        </div>

        {/* Actions */}
        <div className="workflow-actions" style={{ marginTop: '12px' }}>
          <button
            className="ghost-btn"
            type="submit"
            disabled={busy || !valid}
            title={valid ? undefined : 'Asset, quote, and timeframe are required.'}
          >
            {busy ? 'Submitting…' : 'Submit run'}
          </button>
        </div>

        {!valid && (
          <div className="artifact-meta" style={{ marginTop: '6px' }}>
            Asset, quote, and timeframe are required. Custom period requires at least one date.
          </div>
        )}
        {status && (
          <div className={`ops-callout ${status.startsWith('Error') ? 'tone-negative' : 'tone-positive'}`} style={{ marginTop: '10px' }}>
            {status}
          </div>
        )}
      </form>
    </section>
  );
}

// ── Direct YAML tab (existing Quick Launch form, preserved unchanged) ──────────

const EXPERIMENTS_CONFIG_DIR = 'configs/experiments';
const CUSTOM_CONFIG_VALUE = '__custom__';

type ConfigOption = {
  name: string;
  path: string;
};

function DirectYamlTab({ serverUrl, onRefresh }: { serverUrl: string | null; onRefresh: () => void }) {
  const [command, setCommand] = useState<'run' | 'sweep'>('sweep');
  const [configPath, setConfigPath] = useState('');
  const [configOptions, setConfigOptions] = useState<ConfigOption[]>([]);
  const [configSelection, setConfigSelection] = useState(CUSTOM_CONFIG_VALUE);
  const [configLoadStatus, setConfigLoadStatus] = useState<'loading' | 'ready' | 'empty'>('loading');
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadConfigs() {
      try {
        const listing = await window.quantlabDesktop.listDirectory(EXPERIMENTS_CONFIG_DIR, 1);
        const options = (listing.entries || [])
          .filter((entry: any) => entry.kind === 'file' && /\.(ya?ml|json)$/i.test(entry.name || ''))
          .map((entry: any) => ({
            name: entry.relative_path || entry.name,
            path: entry.relative_path || entry.path || entry.name,
          }))
          .sort((left: ConfigOption, right: ConfigOption) => left.path.localeCompare(right.path));
        if (cancelled) return;
        setConfigOptions(options);
        setConfigLoadStatus(options.length ? 'ready' : 'empty');
        if (options.length && !configPath.trim()) {
          setConfigSelection(options[0].path);
          setConfigPath(options[0].path);
        }
      } catch (_err) {
        if (cancelled) return;
        setConfigOptions([]);
        setConfigSelection(CUSTOM_CONFIG_VALUE);
        setConfigLoadStatus('empty');
      }
    }
    loadConfigs();
    return () => {
      cancelled = true;
    };
  }, []);

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

  return (
    <section className="artifact-panel">
      <div className="section-label">Direct YAML</div>
      <h3>Submit from config file</h3>
      <p className="artifact-meta" style={{ marginBottom: '14px' }}>
        Select or enter an existing config path and submit directly.
        Direct YAML file preview is added in a follow-up slice.
      </p>
      <div className={`ops-callout ${serverUrl ? 'tone-positive' : 'tone-warning'}`}>
        {serverUrl
          ? 'Backend: Online - ready to submit jobs'
          : 'Backend: Offline - job submission may be unavailable'}
      </div>
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
                  const nextValue = e.target.value;
                  setConfigSelection(nextValue);
                  setConfigPath(nextValue === CUSTOM_CONFIG_VALUE ? '' : nextValue);
                }}
                disabled={busy}
              >
                {configOptions.map((option) => (
                  <option key={option.path} value={option.path}>{option.path}</option>
                ))}
                <option value={CUSTOM_CONFIG_VALUE}>Custom path...</option>
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
          </div>
        )}
        <div className="workflow-actions" style={{ marginTop: '12px' }}>
          <button className="ghost-btn" type="submit" disabled={busy || (command === 'sweep' && !configPath.trim())}>
            {busy ? 'Submitting…' : 'Submit'}
          </button>
          {serverUrl && (
            <button
              className="ghost-btn"
              type="button"
              onClick={() => {
                if (typeof window.quantlabDesktop?.openExternal === 'function') {
                  window.quantlabDesktop.openExternal(`${serverUrl.replace(/\/$/, '')}/research_ui/index.html#/launch`);
                }
              }}
            >
              Full browser form
            </button>
          )}
        </div>
        {!serverUrl && (
          <div className="artifact-meta" style={{ marginTop: '10px' }}>
            Submit remains available, but the backend may need to be started manually before the job can be accepted.
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
        <SummaryCard
          label="Total jobs"
          value={formatCount(totalJobs)}
          tone={totalJobs ? 'tone-positive' : 'tone-warning'}
        />
        <SummaryCard
          label="In flight"
          value={formatCount(inFlightCount)}
          tone={inFlightCount ? 'tone-warning' : ''}
        />
        <SummaryCard
          label="Failed"
          value={formatCount(failedCount)}
          tone={failedCount ? 'tone-negative' : 'tone-positive'}
        />
        <SummaryCard
          label="Latest run"
          value={latestRun?.run_id ?? 'None'}
          tone={latestRun?.run_id ? 'tone-positive' : 'tone-warning'}
        />
        <SummaryCard
          label="Browser bridge"
          value={serverUrl ? 'Available' : 'Unavailable'}
          tone={serverUrl ? 'tone-positive' : 'tone-warning'}
        />
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
            <GuidedBuilderTab serverUrl={serverUrl} onRefresh={refreshRegistry} />
          )}
          {activeBuilderTab === 'direct-yaml' && (
            <DirectYamlTab serverUrl={serverUrl} onRefresh={refreshRegistry} />
          )}
        </div>
      </div>
    </div>
  );
}
