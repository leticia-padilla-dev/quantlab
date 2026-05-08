import React, { useMemo, useState, useEffect } from 'react';
import { useQuantLab } from './QuantLabContext';
import {
  formatCount,
  formatPercent,
  formatNumber,
  formatDateTime,
  titleCase,
  toneClass,
  shortCommit,
} from '../modules/utils';
import { renderActionRow, renderActionButton } from '../modules/view-primitives';
import './RunsPane.css';

/**
 * RunsPane — Main workstation for indexed runs, selection, and decision queue.
 * Mirrors renderRunsTab() from app-legacy.js.
 */
export function RunsPane({ tab }) {
  const {
    state,
    getRuns,
    getLatestRun,
    getSelectedRuns,
    findRun,
    decision,
    toggleCandidate,
    setBaseline,
    toggleShortlist,
    openTab,
    refreshRegistry,
  } = useQuantLab();

  const runs = getRuns();
  const latestRun = getLatestRun();
  const selectedRuns = getSelectedRuns();
  const baselineRun = state.candidatesStore?.baseline_run_id
    ? findRun(state.candidatesStore.baseline_run_id)
    : null;
  const spotlightRun = selectedRuns[0] || baselineRun || latestRun || null;

  const candidateEntries = decision.getCandidateEntriesResolved();
  const shortlistCount = candidateEntries.filter(
    (e) => e.shortlisted && e.run
  ).length;
  const compareReady = shortlistCount + (state.candidatesStore?.baseline_run_id ? 1 : 0) >= 2;

  const paper = state.snapshot?.paperHealth || null;
  const backendOnline = Boolean(state.workspace?.serverUrl);

  return (
    <div className="tab-shell runs-tab">
      {/* Header section with description and action buttons */}
      <div className="artifact-top">
        <div>
          <div className="section-label">Run explorer</div>
          <h3>Runs</h3>
          <div className="artifact-meta">
            Primary workstation for indexed runs, local evidence, shortlist state,
            and operational continuity.
          </div>
          <div className="artifact-meta">
            <span className={backendOnline ? 'tone-positive' : 'tone-warning'}>
              Backend: {backendOnline ? 'Online' : 'Offline'}
            </span>
            {' · '}
            <span className={runs.length ? 'tone-positive' : 'tone-warning'}>
              Index: {formatCount(runs.length)} runs
            </span>
          </div>
        </div>
        <div className="artifact-actions">
          <button
            className="ghost-btn"
            onClick={() => refreshRegistry?.()}
          >
            Refresh runs
          </button>
          <button
            className="ghost-btn"
            onClick={() => openTab({ kind: 'launch', title: 'Launch', href: '#/launch' })}
          >
            Open launch surface
          </button>
          <button
            className="ghost-btn"
            onClick={() => openTab({ kind: 'candidates' })}
          >
            Open candidates
          </button>
          <button
            className="ghost-btn"
            onClick={() => openTab({ kind: 'paper' })}
          >
            Open paper ops
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="tab-summary-grid">
        <SummaryCard
          label="Indexed runs"
          value={formatCount(runs.length)}
          tone={runs.length ? 'tone-positive' : 'tone-warning'}
        />
        <SummaryCard
          label="Candidates"
          value={formatCount(candidateEntries.length)}
          tone={candidateEntries.length ? 'tone-warning' : ''}
        />
        <SummaryCard
          label="Shortlisted"
          value={formatCount(shortlistCount)}
          tone={shortlistCount ? 'tone-positive' : ''}
        />
        <SummaryCard
          label="Baseline"
          value={state.candidatesStore?.baseline_run_id || 'Unset'}
          tone={state.candidatesStore?.baseline_run_id ? 'tone-positive' : 'tone-warning'}
        />
        <SummaryCard
          label="Paper state"
          value={paper?.available ? 'Ready' : 'Pending'}
          tone={paper?.available ? 'tone-positive' : 'tone-warning'}
        />
      </div>

      {/* Runs workbench: table + sidebar */}
      <div className="runs-workbench">
        <div className="runs-workbench-main">
          <RunsTable runs={runs} />
        </div>
        <aside className="runs-workbench-side">
          {spotlightRun && (
            <RunsSpotlightCard
              run={spotlightRun}
              baselineId={state.candidatesStore?.baseline_run_id}
            />
          )}
          <RunsDecisionQueueCard
            candidateCount={candidateEntries.length}
            shortlistCount={shortlistCount}
            compareReady={compareReady}
            selectedRunIds={state.selectedRunIds}
          />
        </aside>
      </div>
    </div>
  );
}

/**
 * Summary card component
 */
function SummaryCard({ label, value, tone = '' }) {
  return (
    <article className={`summary-card ${tone || ''}`}>
      <div className="label">{label}</div>
      <div className={`value ${tone || ''}`}>{value}</div>
    </article>
  );
}

/**
 * Runs table with selection, metrics, and actions
 */
function RunsTable({ runs }) {
  const { state, decision, navigateToSurface, refreshRegistry } = useQuantLab();

  if (!runs.length) {
    const serverUrl = state.workspace?.serverUrl
      ? String(state.workspace.serverUrl).replace(/\/$/, '')
      : '';
    const backendOnline = Boolean(serverUrl);
    return (
      <div className="empty-state" data-smoke="empty-runs-recovery">
        <div className="section-label">No indexed runs found</div>
        <p>
          React reads QuantLab evidence from <code>outputs/runs/runs_index.json</code>.
          The shell is empty because no run index is available yet, or the index exists
          with no runs.
        </p>
        <div className="workflow-actions" style={{ marginTop: '12px' }}>
          <button className="ghost-btn" type="button" onClick={() => refreshRegistry?.()}>
            Refresh run registry
          </button>
          <button className="ghost-btn" type="button" onClick={() => navigateToSurface('launch')}>
            Open Launch
          </button>
          {backendOnline && (
            <button
              className="ghost-btn"
              type="button"
              onClick={() => window.quantlabDesktop?.openExternal?.(`${serverUrl}/research_ui/index.html#/launch`)}
            >
              Open browser launch
            </button>
          )}
        </div>
        {!backendOnline && (
          <div className="artifact-meta" style={{ marginTop: '10px' }}>
            Backend unavailable. Refresh may not work until the server is restarted.
          </div>
        )}
      </div>
    );
  }

  return (
    <div id="workflow-runs-list" className="runs-table">
      <table>
        <thead>
          <tr>
            <th className="col-select">Select</th>
            <th className="col-id">Run ID</th>
            <th className="col-mode">Mode</th>
            <th className="col-metrics">Metrics</th>
            <th className="col-status">Status</th>
            <th className="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <RunRow
              key={run.run_id}
              run={run}
              isSelected={state.selectedRunIds.includes(run.run_id)}
              isCandidate={decision.isCandidateRun(run.run_id)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Async loader for robustness verdict status — only fires for walkforward runs.
 * Returns 'pass' | 'fail' | 'review' | null (null = not loaded or not applicable).
 * Does not block render; badge appears when artifact is ready.
 */
function useRobustnessVerdictStatus(run) {
  const [status, setStatus] = useState(null);

  const isWalkforward = useMemo(() => {
    const mode = String(run?.mode || '').toLowerCase();
    const runId = String(run?.run_id || '').toLowerCase();
    return mode.includes('walkforward') || mode.includes('walk-forward') || runId.includes('walkforward');
  }, [run?.mode, run?.run_id]);

  useEffect(() => {
    if (!isWalkforward || !run?.path) return;
    let cancelled = false;
    const verdictPath = `${String(run.path).replace(/[\\/]+$/, '')}/robustness_verdict.json`;
    window.quantlabDesktop?.readProjectJson?.(verdictPath)
      .then((verdict) => {
        if (!cancelled && verdict?.status) setStatus(String(verdict.status).toLowerCase());
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [isWalkforward, run?.path]);

  return status;
}

/**
 * Individual run row in table
 */
function RunRow({ run, isSelected, isCandidate }) {
  const { state, toggleRunSelection, toggleCandidate, openTab } = useQuantLab();
  const disableSelection =
    !isSelected && state.selectedRunIds.length >= 4;
  const verdictStatus = useRobustnessVerdictStatus(run);

  return (
    <tr className={isSelected ? 'selected' : ''}>
      <td className="col-select">
        <input
          type="checkbox"
          checked={isSelected}
          disabled={disableSelection}
          onChange={() => toggleRunSelection(run.run_id)}
          data-select-run={run.run_id}
        />
      </td>
      <td className="col-id">
        <strong>{run.run_id}</strong>
      </td>
      <td className="col-mode">{titleCase(run.mode || 'unknown')}</td>
      <td className="col-metrics">
        <span className="metric">
          Return: {formatPercent(run.total_return)}
        </span>
        <span className="metric">
          Sharpe: {formatNumber(run.sharpe_simple)}
        </span>
      </td>
      <td className="col-status">
        {isCandidate && <span className="badge candidate">Candidate</span>}
        {verdictStatus && (
          <span className={`badge verdict-badge verdict-${verdictStatus}`}>
            {verdictStatus.toUpperCase()}
          </span>
        )}
      </td>
      <td className="col-actions">
        <div className="run-row-actions">
          <button
            className="ghost-btn mini"
            onClick={() => openTab({ kind: 'run', runId: run.run_id })}
            data-open-run={run.run_id}
          >
            Open
          </button>
          <button
            className="ghost-btn mini"
            onClick={() => openTab({ kind: 'artifacts', runId: run.run_id, title: `${run.run_id} artifacts`, subview: 'artifacts' })}
            data-open-artifacts={run.run_id}
          >
            Explore
          </button>
          <button
            className="ghost-btn mini"
            onClick={() => toggleCandidate(run.run_id)}
          >
            {isCandidate ? 'Unmark' : 'Mark'}
          </button>
        </div>
      </td>
    </tr>
  );
}

/**
 * Spotlight card showing selected/baseline/latest run detail
 */
function RunsSpotlightCard({ run, baselineId }) {
  const { decision } = useQuantLab();
  const isBaseline = run?.run_id === baselineId;

  return (
    <div className="artifact-panel run-spotlight-card">
      <div className="section-label">Spotlight</div>
      <h3>{run?.run_id || 'None'}</h3>
      {isBaseline && <span className="badge baseline">Baseline</span>}
      <dl className="metric-list">
        <dt>Return</dt>
        <dd>{formatPercent(run?.total_return)}</dd>
        <dt>Sharpe</dt>
        <dd>{formatNumber(run?.sharpe_simple)}</dd>
        <dt>Drawdown</dt>
        <dd>{formatPercent(run?.max_drawdown)}</dd>
      </dl>
    </div>
  );
}

/**
 * Decision queue card showing candidate/shortlist/comparison readiness
 */
function RunsDecisionQueueCard({ candidateCount, shortlistCount, compareReady, selectedRunIds }) {
  const { decision, openTab } = useQuantLab();
  const selectionReady = (selectedRunIds || []).length >= 2;
  const isEnabled = compareReady || selectionReady;

  return (
    <div className="artifact-panel">
      <div className="section-label">Decision queue</div>
      <h3>Selection state</h3>
      <dl className="metric-list">
        <dt>Candidates</dt>
        <dd>{formatCount(candidateCount)}</dd>
        <dt>Shortlisted</dt>
        <dd>{formatCount(shortlistCount)}</dd>
        <dt>Compare ready</dt>
        <dd>{compareReady ? 'Yes' : 'No'}</dd>
      </dl>
      <div style={{ marginTop: '15px' }}>
        <button
          id="workflow-open-compare"
          className="ghost-btn"
          disabled={!isEnabled}
          onClick={() => {
            if (selectionReady && !compareReady) {
              openTab({ kind: 'compare', runIds: selectedRunIds });
            } else {
              openTab({ kind: 'compare', runIds: decision.getDecisionCompareRunIds(), label: 'decision runs' });
            }
          }}
        >
          Compare
        </button>
      </div>
    </div>
  );
}
