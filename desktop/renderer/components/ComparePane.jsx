import React, { useState, useEffect, useMemo } from 'react';
import { loadRunDetailNative } from '../modules/run-detail-loader.js';
import { useQuantLab } from './QuantLabContext';
import {
  formatCount,
  formatPercent,
  formatNumber,
  rankRunsByMetric,
  collectConfigDeltas,
  titleCase,
  toneClass,
  formatMetricForDisplay,
} from '../modules/utils';
import './ComparePane.css';

const RANK_METRICS = [
  'sharpe_simple',
  'total_return',
  'max_drawdown',
  'trades',
];

/**
 * ComparePane — Decision-oriented multi-run comparison.
 * Mirrors renderCompareTab() from app-legacy.js.
 */
export function ComparePane({ tab }) {
  const { findRun, decision, navigateToSurface, updateTab, openTab } = useQuantLab();
  const [detailMap, setDetailMap] = useState(tab.detailMap || {});
  const [loading, setLoading] = useState(tab.status === 'loading');
  const [rankMetric, setRankMetric] = useState(tab.rankMetric || 'sharpe_simple');
  const [focusRunId, setFocusRunId] = useState(null);

  // Recalculates on registry refresh or tab.runIds change
  const runs = useMemo(
    () => (tab.runIds || []).map(findRun).filter(Boolean),
    [tab.runIds, findRun]
  );

  // Prune stale runIds so persisted compare tabs self-heal after index changes
  useEffect(() => {
    const ids = tab.runIds || [];
    const validIds = ids.filter((id) => findRun(id) !== null);
    if (validIds.length !== ids.length) {
      updateTab(tab.id, { runIds: validIds });
    }
  }, [tab.id, tab.runIds, findRun, updateTab]);

  // Load run details on mount if not already loaded
  useEffect(() => {
    if (loading && tab.runIds?.length) {
      (async () => {
        try {
          const details = await Promise.all(
            tab.runIds.map(async (runId) => {
              try {
                const run = findRun(runId);
                const detail = run ? await loadRunDetailNative(run) : null;
                return [runId, detail];
              } catch (_err) {
                return [runId, null];
              }
            })
          );
          setDetailMap(Object.fromEntries(details));
          setLoading(false);
        } catch (_err) {
          setLoading(false);
        }
      })();
    }
  }, [tab.runIds, loading, findRun]);

  useEffect(() => {
    if (tab.rankMetric !== rankMetric) {
      updateTab(tab.id, { rankMetric });
    }
  }, [tab.id, tab.rankMetric, rankMetric, updateTab]);

  if (runs.length < 2) {
    const orphanedCount = (tab.runIds || []).length - runs.length;
    const isEmpty = !tab.runIds || tab.runIds.length === 0;
    const shortlistIds = decision.getDecisionCompareRunIds();
    const shortlistReady = shortlistIds.length >= 2;
    return (
      <div className="empty-state" data-smoke="compare-stale-recovery">
        <div className="section-label">
          {isEmpty ? 'No compare set selected' : 'Compare set unavailable'}
        </div>
        <p>
          {isEmpty
            ? 'Select at least 2 runs to compare.'
            : orphanedCount > 0
              ? `${orphanedCount} run${orphanedCount !== 1 ? 's' : ''} in this compare set ${orphanedCount !== 1 ? 'are' : 'is'} no longer available in the registry.`
              : 'This compare set needs at least 2 runs.'}
        </p>
        <div className="workflow-actions" style={{ marginTop: '12px' }}>
          {shortlistReady && (
            <button
              className="ghost-btn"
              type="button"
              onClick={() => openTab({ kind: 'compare', runIds: shortlistIds })}
            >
              Compare shortlist
            </button>
          )}
          <button
            className="ghost-btn"
            type="button"
            onClick={() => navigateToSurface('candidates')}
          >
            Go to Candidates
          </button>
          <button
            className="ghost-btn"
            type="button"
            onClick={() => navigateToSurface('runs')}
          >
            Go to Runs
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="tab-placeholder">
        Preparing decision-oriented compare for {runs.length} runs...
      </div>
    );
  }

  const rankedRuns = rankRunsByMetric(runs, rankMetric);
  const configDeltaEntries = collectConfigDeltas(runs, detailMap);

  const baselineInSet = runs.find((r) =>
    decision.isBaselineRun(r.run_id)
  ) || null;
  const shortlistedCount = runs.filter((r) =>
    decision.isShortlistedRun(r.run_id)
  ).length;

  const robustnessArtifactCount = runs.filter((r) =>
    Boolean(detailMap?.[r.run_id]?.robustnessVerdict)
  ).length;

  useEffect(() => {
    const nextFocusId = baselineInSet?.run_id || rankedRuns[0]?.run_id || null;
    setFocusRunId((current) => {
      if (!current) return nextFocusId;
      if (runs.some((r) => r.run_id === current)) return current;
      return nextFocusId;
    });
  }, [baselineInSet?.run_id, rankedRuns, runs]);

  const focusRun = focusRunId
    ? runs.find((r) => r.run_id === focusRunId) || null
    : null;
  const focusDetail = focusRun ? (detailMap?.[focusRun.run_id] || null) : null;
  const focusStrategy = getRunStrategyLabel(focusDetail);
  const focusScope = getRunScopeLabel(focusDetail);
  const focusRobustness = robustnessBadge(focusDetail?.robustnessVerdict);

  return (
    <div className="compare-shell compare-tab">
      <div className="tab-summary-grid">
        <SummaryCard label="Runs" value={String(runs.length)} />
        <SummaryCard
          label="Rank metric"
          value={titleCase(rankMetric.replace('_', ' '))}
        />
        <SummaryCard
          label="Baseline"
          value={baselineInSet ? baselineInSet.run_id : '—'}
        />
        <SummaryCard label="Shortlisted" value={String(shortlistedCount)} />
        <SummaryCard label="Robustness artifacts" value={String(robustnessArtifactCount)} />
        <SummaryCard label="Config deltas" value={String(configDeltaEntries.length)} />
      </div>

      <div className="compare-workbench">
        <div className="compare-workbench-main">
          <div className="artifact-panel">
            <div className="section-label">Compare table</div>
            <h3>Research-oriented comparison</h3>
            <div className="artifact-meta">
              Compare runs using existing artifacts and recorded metrics.
            </div>
            <CompareRankingTable
              runs={runs}
              rankMetric={rankMetric}
              detailMap={detailMap}
              focusRunId={focusRunId}
              onFocusRunId={setFocusRunId}
              onRankMetric={setRankMetric}
            />
          </div>
        </div>

        <aside className="compare-workbench-side">
          <div className="artifact-panel compare-focus-card">
            <div className="section-label">Focus run</div>
            <h3>{focusRun ? focusRun.run_id : '—'}</h3>
            <div className="artifact-meta">
              {focusStrategy}{focusScope ? ` · ${focusScope}` : ''}
            </div>
            <div className="compare-focus-actions">
              {focusRun && (
                <>
                  <button className="ghost-btn mini" type="button" onClick={() => openTab({ kind: 'run', runId: focusRun.run_id })}>
                    Inspect
                  </button>
                  <button className="ghost-btn mini" type="button" onClick={() => openTab({ kind: 'artifacts', runId: focusRun.run_id, title: `${focusRun.run_id} artifacts`, subview: 'artifacts' })}>
                    Artifacts
                  </button>
                </>
              )}
            </div>
            <dl className="metric-list compact">
              <dt>Robustness</dt>
              <dd className={focusRobustness.cls}>{focusRobustness.label}</dd>
              <dt>Return</dt>
              <dd className={focusRun ? toneClass(focusRun.total_return, true) : ''}>
                {focusRun ? formatPercent(focusRun.total_return) : '—'}
              </dd>
              <dt>Sharpe</dt>
              <dd>{focusRun ? formatNumber(focusRun.sharpe_simple) : '—'}</dd>
              <dt>Drawdown</dt>
              <dd className={focusRun ? toneClass(focusRun.max_drawdown, false) : ''}>
                {focusRun ? formatPercent(focusRun.max_drawdown) : '—'}
              </dd>
              <dt>Trades</dt>
              <dd>{focusRun ? formatCount(focusRun.trades) : '—'}</dd>
            </dl>
          </div>

          <div className="artifact-panel">
            <div className="section-label">Config deltas</div>
            <h3>Resolved differences</h3>
            {configDeltaEntries.length ? (
              <div className="mini-table">
                <div className="mini-table-row head">
                  <span>Key</span>
                  <span>Values</span>
                </div>
                {configDeltaEntries.map(([key, values]) => (
                  <div key={key} className="mini-table-row">
                    <span className="compare-delta-key">{key}</span>
                    <span className="compare-delta-values">
                      {values.map((value) => (
                        <span key={value} className="compare-delta-value">{value}</span>
                      ))}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                No resolved config deltas for this compare set.
              </div>
            )}
          </div>
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
 * Ranking table showing all runs ranked by selected metric
 */
function CompareRankingTable({ runs, rankMetric, detailMap, focusRunId, onFocusRunId, onRankMetric }) {
  const { decision, toggleCandidate, setBaseline, toggleShortlist, openTab } = useQuantLab();

  const rankedRuns = useMemo(() => rankRunsByMetric(runs, rankMetric), [runs, rankMetric]);

  return (
    <div className="compare-ranking-table">
      <div className="metric-selector">
        <label htmlFor="rank-metric">Rank by:</label>
        <select
          id="rank-metric"
          value={rankMetric}
          onChange={(e) => onRankMetric(e.target.value)}
        >
          {RANK_METRICS.map((metric) => (
            <option key={metric} value={metric}>
              {titleCase(metric.replace('_', ' '))}
            </option>
          ))}
        </select>
      </div>

      <table className="runs-compare-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Run ID</th>
            <th>Strategy</th>
            <th>Scope</th>
            <th>Robustness</th>
            <th className="metric-col">{titleCase(rankMetric.replace('_', ' '))}</th>
            <th>Return</th>
            <th>Sharpe</th>
            <th>Drawdown</th>
            <th>Trades</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rankedRuns.map((run, idx) => (
            <tr
              key={run.run_id}
              className={`${decision.isBaselineRun(run.run_id) ? 'is-baseline' : ''} ${focusRunId === run.run_id ? 'is-focus' : ''}`}
              onClick={() => onFocusRunId(run.run_id)}
            >
              <td className="rank">{idx + 1}</td>
              <td className="run-id">{run.run_id}</td>
              <td className="run-strategy">{getRunStrategyLabel(detailMap?.[run.run_id] || null)}</td>
              <td className="run-scope">{getRunScopeLabel(detailMap?.[run.run_id] || null)}</td>
              <td className="run-robustness">
                <span className={`robustness-chip ${robustnessBadge(detailMap?.[run.run_id]?.robustnessVerdict).cls}`}>
                  {robustnessBadge(detailMap?.[run.run_id]?.robustnessVerdict).label}
                </span>
              </td>
              <td
                className={`metric-col ${
                  rankMetric === 'max_drawdown'
                    ? toneClass(run.max_drawdown, false)
                    : toneClass(run[rankMetric], true)
                }`}
              >
                {formatMetricForDisplay(run[rankMetric], rankMetric)}
              </td>
              <td className={toneClass(run.total_return, true)}>
                {formatPercent(run.total_return)}
              </td>
              <td>{formatNumber(run.sharpe_simple)}</td>
              <td className={toneClass(run.max_drawdown, false)}>
                {formatPercent(run.max_drawdown)}
              </td>
              <td>{formatCount(run.trades)}</td>
              <td className="actions">
                <div className="compare-row-actions">
                  <button
                    className="ghost-btn mini"
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      openTab({ kind: 'run', runId: run.run_id });
                    }}
                  >
                    Inspect
                  </button>
                  <button
                    className="ghost-btn mini"
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleCandidate(run.run_id);
                    }}
                  >
                    {decision.isCandidateRun(run.run_id) ? 'Unmark' : 'Mark'}
                  </button>
                  <button
                    className="ghost-btn mini"
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleShortlist(run.run_id);
                    }}
                  >
                    {decision.isShortlistedRun(run.run_id) ? 'Remove' : 'Shortlist'}
                  </button>
                  <button
                    className="ghost-btn mini"
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setBaseline(run.run_id);
                    }}
                  >
                    Baseline
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function getRunStrategyLabel(detail) {
  const name = detail?.report?.config_received?.strategy?.strategy_name;
  if (typeof name === 'string' && name.trim()) return name.trim();
  return '—';
}

function getRunScopeLabel(detail) {
  const tickers = detail?.report?.config_received?.data?.tickers;
  if (Array.isArray(tickers) && tickers.length) return tickers.join(', ');
  return '—';
}

function robustnessBadge(verdict) {
  const status = String(verdict?.status || '').toLowerCase();
  if (status === 'pass') return { label: 'Pass', cls: 'up' };
  if (status === 'review') return { label: 'Review', cls: 'warn' };
  if (status === 'fail') return { label: 'Fail', cls: 'down' };
  return { label: '—', cls: 'muted' };
}
