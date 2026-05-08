import React from 'react';
import type { ExecutionTab } from '../../shared/models/tab';
import type { SnapshotStatus } from '../../shared/models/snapshot';
import { useSnapshot } from '../hooks/useSnapshot.js';
import { useQuantLab as _useQuantLab } from './QuantLabContext';

// QuantLabContext is a JS file; cast to any so strict-mode TSX can consume it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const useQuantLab = _useQuantLab as () => any;

const DEFAULT_RESEARCH_UI_SERVER_URL = 'http://127.0.0.1:8000';

const ARTIFACT_TYPES = [
  ['preflight', 'Preflight'],
  ['account_readiness', 'Account readiness'],
  ['signed_action', 'Signed action'],
  ['submit_response', 'Submit response'],
  ['order_status', 'Order status'],
  ['continuous_supervision', 'Continuous supervision'],
] as const;

function fmt(n: number | null | undefined): string {
  if (n == null || isNaN(Number(n))) return '0';
  return String(Number(n));
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return 'Never';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function truncate(text: string, maxChars: number): string {
  if (!text) return '—';
  if (text.length <= maxChars) return text;
  return '…' + text.slice(text.length - maxChars);
}

function titleCase(s: string): string {
  return String(s || 'unknown').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function statusTone(status: string | null | undefined): string {
  const value = String(status ?? '').toLowerCase();
  if (!value || value === '—' || value === 'unknown') return 'tone-warning';
  if (value === 'ok' || value === 'filled' || value === 'signed') return 'tone-positive';
  if (value === 'critical' || value.includes('fail') || value.includes('error') || value.includes('alert')) return 'tone-negative';
  return 'tone-warning';
}

function parentPath(targetPath: string | null | undefined): string | null {
  if (!targetPath) return null;
  const normalized = String(targetPath).replace(/\\/g, '/');
  const idx = normalized.lastIndexOf('/');
  return idx > 0 ? normalized.slice(0, idx) : null;
}

function latestSessionStatus(
  submitState: string,
  orderState: string,
  artifactState: string,
  signatureState: string,
): { label: string; tone: string; detail: string } {
  const submit = submitState.toLowerCase();
  const order = orderState.toLowerCase();
  const artifact = artifactState.toLowerCase();
  const signature = signatureState.toLowerCase();

  if (order === 'filled' && artifact === 'filled' && signature === 'signed') {
    return {
      label: 'Evidence complete',
      tone: 'tone-positive',
      detail: 'Latest session artifacts show filled order evidence with a signed action trail.',
    };
  }
  if (submit.includes('reject') || order.includes('reject') || artifact.includes('fail')) {
    return {
      label: 'Review required',
      tone: 'tone-negative',
      detail: 'Latest session contains a rejected or failed state. Inspect the artifacts before continuing.',
    };
  }
  return {
    label: 'Review',
    tone: 'tone-warning',
    detail: 'Latest session is not terminally clear from the displayed fields. Inspect the artifacts.',
  };
}

function alertCode(alert: any): string {
  return String(alert?.alert_code ?? alert?.code ?? 'UNKNOWN_ALERT');
}

function alertSessionId(alert: any): string | null {
  const value = alert?.session_id ?? alert?.submit_session_id ?? null;
  return value ? String(value) : null;
}

function alertTone(alert: any): string {
  const severity = String(alert?.severity ?? '').toLowerCase();
  const code = alertCode(alert).toLowerCase();
  if (severity === 'critical' || code.includes('rejected') || code.includes('failed') || code.includes('missing')) {
    return 'tone-negative';
  }
  if (severity === 'warning' || code.includes('unknown') || code.includes('attention') || code.includes('canceled')) {
    return 'tone-warning';
  }
  return 'tone-positive';
}

function alertExplanation(alert: any): string {
  const message = typeof alert?.message === 'string' ? alert.message.trim() : '';
  if (message) return message;

  const code = alertCode(alert);
  if (code.includes('RECONCILIATION')) return 'Reconciliation evidence is incomplete or ambiguous for this submit session.';
  if (code.includes('REJECTED')) return 'A submit or remote order was rejected and remains preserved as corridor evidence.';
  if (code.includes('CANCEL')) return 'A cancel-related artifact requires review before interpreting this session as clean.';
  if (code.includes('SUPERVISION')) return 'Continuous supervision marked this session for operator attention.';
  if (code.includes('ORDER_STATUS')) return 'Order status evidence is missing or unknown for this submit session.';
  if (code.includes('SIGN')) return 'Signing evidence is missing, unsigned, or mismatched for this submit session.';
  return 'Core emitted this corridor alert. Inspect the linked session artifacts before interpreting the current execution state.';
}

function artifactState(artifact: any): { label: string; tone: string } {
  if (!artifact) return { label: 'Missing', tone: 'tone-warning' };
  const value =
    artifact.normalized_state ??
    artifact.submit_state ??
    artifact.signature_state ??
    artifact.readiness_allowed ??
    artifact.market_supported ??
    artifact.response_type ??
    artifact.artifact_type ??
    'Available';
  const label = typeof value === 'boolean'
    ? (value ? 'True' : 'False')
    : titleCase(String(value));
  return { label, tone: statusTone(String(value)) };
}

function copyText(text: string, setCopyStatus: (value: string | null) => void, label = 'Copied path') {
  if (!text || typeof navigator?.clipboard?.writeText !== 'function') return;
  void navigator.clipboard.writeText(text).then(() => {
    setCopyStatus(label);
    window.setTimeout(() => setCopyStatus(null), 1800);
  });
}

function SummaryCard({ label, value, tone = '' }: { label: string; value: string; tone?: string }) {
  return (
    <article className={`summary-card ${tone}`}>
      <div className="label" title={label}>{label}</div>
      <div className={`value ${tone}`} title={value}>{value}</div>
    </article>
  );
}

function MetricRow({ label, value, tone = '' }: { label: string; value: string; tone?: string }) {
  return (
    <div className={tone}>
      <dt title={label}>{label}</dt>
      <dd title={value}>{value}</dd>
    </div>
  );
}

function AlertListPanel({
  alerts,
  setCopyStatus,
}: {
  alerts: any[];
  setCopyStatus: (value: string | null) => void;
}) {
  const visibleAlerts = alerts.slice(0, 5);

  return (
    <section className="artifact-panel execution-panel execution-alerts-panel">
      <div className="section-label">Latest alerts</div>
      <h3>Corridor alert evidence</h3>
      <p className="artifact-meta execution-alert-note">
        Alerts are Core-generated and historical. A preserved critical alert can keep the root corridor status elevated
        even when the latest session fields look complete.
      </p>
      {visibleAlerts.length === 0 ? (
        <div className="empty-state compact">No corridor alerts are currently reported.</div>
      ) : (
        <div className="execution-alert-list">
          {visibleAlerts.map((alert, index) => {
            const code = alertCode(alert);
            const sessionId = alertSessionId(alert);
            const tone = alertTone(alert);
            const alertPath = alert?.path ? String(alert.path) : null;
            return (
              <article className={`execution-alert-row ${tone}`} key={`${code}-${sessionId ?? index}`}>
                <div className="execution-alert-main">
                  <span className={`execution-alert-pill ${tone}`}>{titleCase(alert?.severity ?? 'alert')}</span>
                  <strong title={code}>{code}</strong>
                </div>
                <div className="execution-alert-meta">
                  <span title={sessionId ?? ''}>Session {sessionId ?? '—'}</span>
                  <span>{fmtDate(alert?.activity_at)}</span>
                </div>
                <p>{alertExplanation(alert)}</p>
                <div className="execution-alert-actions">
                  <button
                    className="ghost-btn mini"
                    type="button"
                    disabled={!alertPath}
                    onClick={() => alertPath && window.quantlabDesktop?.openPath?.(alertPath)}
                  >
                    Open
                  </button>
                  <button
                    className="ghost-btn mini"
                    type="button"
                    disabled={!sessionId || typeof navigator?.clipboard?.writeText !== 'function'}
                    onClick={() => sessionId && copyText(sessionId, setCopyStatus, 'Copied alert session id')}
                  >
                    Copy id
                  </button>
                  <button
                    className="ghost-btn mini"
                    type="button"
                    disabled={!alertPath || typeof navigator?.clipboard?.writeText !== 'function'}
                    onClick={() => alertPath && copyText(alertPath, setCopyStatus, 'Copied alert path')}
                  >
                    Copy path
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
      {alerts.length > visibleAlerts.length && (
        <div className="artifact-meta">Showing {visibleAlerts.length} of {alerts.length} alerts.</div>
      )}
    </section>
  );
}

function ArtifactListPanel({
  artifacts,
  setCopyStatus,
}: {
  artifacts: Record<string, any>;
  setCopyStatus: (value: string | null) => void;
}) {
  return (
    <section className="artifact-panel execution-panel execution-artifacts-panel">
      <div className="section-label">Artifact list</div>
      <h3>Supervised corridor evidence</h3>
      <div className="execution-artifact-list">
        {ARTIFACT_TYPES.map(([key, label]) => {
          const artifact = artifacts?.[key] ?? null;
          const state = artifactState(artifact);
          const artifactPath = artifact?.path ?? null;
          return (
            <article className={`execution-artifact-row ${artifact ? '' : 'is-missing'}`} key={key}>
              <div className="execution-artifact-main">
                <strong>{label}</strong>
                <span className={`execution-artifact-state ${state.tone}`}>{state.label}</span>
              </div>
              <div className="execution-artifact-meta">
                <span>{artifact?.generated_at ? fmtDate(artifact.generated_at) : 'No artifact found'}</span>
                <span title={artifactPath ?? ''}>{artifactPath ? truncate(artifactPath, 74) : '—'}</span>
              </div>
              <div className="execution-artifact-actions">
                <button
                  className="ghost-btn mini"
                  type="button"
                  disabled={!artifactPath}
                  onClick={() => artifactPath && window.quantlabDesktop?.openPath?.(artifactPath)}
                >
                  Open
                </button>
                <button
                  className="ghost-btn mini"
                  type="button"
                  disabled={!artifactPath || typeof navigator?.clipboard?.writeText !== 'function'}
                  onClick={() => artifactPath && copyText(artifactPath, setCopyStatus, `Copied ${label} path`)}
                >
                  Copy
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export function ExecutionPane({ tab: _tab }: { tab: ExecutionTab }) {
  const { state } = useQuantLab();
  const [copyStatus, setCopyStatus] = React.useState<string | null>(null);
  const workspace = state.workspace ?? {};
  const workspaceServerUrl = typeof workspace.serverUrl === 'string' ? workspace.serverUrl.trim() : '';
  const native = useSnapshot(state.snapshot != null ? null : (workspaceServerUrl || DEFAULT_RESEARCH_UI_SERVER_URL));
  const snapshotStatus: Partial<SnapshotStatus> = state.snapshotStatus ?? native.snapshotStatus ?? {};
  const snapshot = state.snapshot ?? native.snapshot ?? {};
  const surface = (snapshot as any).hyperliquidSurface ?? null;

  const empty = !surface || !surface.available;
  const health = surface?.submit_health ?? {};
  const alerts: any[] = Array.isArray(surface?.submit_alerts) ? surface.submit_alerts : [];
  const latestAlertCode: string | null = alerts[0] ? alertCode(alerts[0]) : null;
  const alertStatus: string = surface?.submit_alert_status ?? 'unknown';
  const latestArtifact: any =
    surface?.latest_artifacts?.order_status ??
    surface?.latest_artifacts?.submit_response ??
    surface?.latest_artifacts?.continuous_supervision ??
    null;
  const latestArtifacts: Record<string, any> = surface?.latest_artifacts ?? {};
  const latestArtifactPath: string | null = latestArtifact?.path ?? null;
  const latestUpdatedAt: string | null = surface?.latest_ready_generated_at ?? health.latest_submit_at ?? null;
  const signatureState: string = surface?.signature_state ?? 'unknown';
  const latestSubmitState: string = health.latest_submit_state ?? 'unknown';
  const latestOrderState: string = health.latest_order_state ?? 'unknown';
  const latestArtifactState: string = latestArtifact?.normalized_state ?? 'unknown';
  const latestArtifactDir = parentPath(latestArtifactPath);
  const latestSessionDir: string | null = surface?.submit_sessions_root && health.latest_submit_session_id
    ? `${surface.submit_sessions_root}/${health.latest_submit_session_id}`
    : latestArtifactDir;
  const latestSession = latestSessionStatus(latestSubmitState, latestOrderState, latestArtifactState, signatureState);
  const alertTone = empty ? 'tone-warning' : statusTone(alertStatus);

  return (
    <div className="tab-shell execution-pane" data-smoke="surface-execution">
      <div className={`execution-hero ${alertTone}`}>
        <div>
          <div className="section-label">Execution supervision</div>
          <h3>Hyperliquid supervised corridor</h3>
          <p className="corridor-copy">
            Read-only status from QuantLab artifacts. Desktop does not authorize, sign, or submit orders.
          </p>
        </div>
        <div className={`execution-alert-badge ${alertTone}`}>
          <span>Root corridor alert</span>
          <strong>{empty ? 'Unavailable' : titleCase(alertStatus)}</strong>
        </div>
      </div>

      {!empty && alertStatus !== 'ok' && (
        <section className="ops-callout tone-warning execution-explainer">
          <strong>Root alert and latest session are separate.</strong>
          {' '}The root corridor alert can remain {titleCase(alertStatus)} because historical rejected or ambiguous sessions are preserved as evidence.
          Inspect the latest session state below before interpreting the current cycle.
        </section>
      )}

      <div className="tab-summary-grid">
        <SummaryCard label="Root alert" value={empty ? 'Unavailable' : titleCase(alertStatus)} tone={alertTone} />
        <SummaryCard label="Latest session" value={latestSession.label} tone={empty ? 'tone-warning' : latestSession.tone} />
        <SummaryCard label="Latest submit" value={titleCase(latestSubmitState)} tone={statusTone(latestSubmitState)} />
        <SummaryCard label="Latest order" value={titleCase(latestOrderState)} tone={statusTone(latestOrderState)} />
        <SummaryCard label="Artifact state" value={titleCase(latestArtifactState)} tone={statusTone(latestArtifactState)} />
        <SummaryCard label="Signature" value={titleCase(signatureState)} tone={statusTone(signatureState)} />
      </div>

      {empty ? (
        <section className="artifact-panel execution-panel">
          <div className="section-label">Latest evidence</div>
          <h3>No supervised corridor evidence available</h3>
          <div className="empty-state">
            Backend may be offline or no submit sessions exist yet. This surface only displays Core/artifact-backed state.
          </div>
        </section>
      ) : (
        <div className="artifact-grid execution-grid">
          <section className="artifact-panel execution-panel">
            <div className="section-label">Latest session status</div>
            <h3>{health.latest_submit_session_id ?? 'No session id'}</h3>
            <div className={`ops-callout ${latestSession.tone} execution-session-callout`}>
              <strong>{latestSession.label}:</strong> {latestSession.detail}
            </div>
            <dl className="metric-list compact">
              <MetricRow label="Submit state" value={latestSubmitState} tone={statusTone(latestSubmitState)} />
              <MetricRow label="Order state" value={latestOrderState} tone={statusTone(latestOrderState)} />
              <MetricRow label="Artifact state" value={latestArtifactState} tone={statusTone(latestArtifactState)} />
              <MetricRow label="Signature state" value={signatureState} tone={statusTone(signatureState)} />
              <MetricRow label="Last evidence at" value={fmtDate(latestUpdatedAt)} />
            </dl>
          </section>

          <section className="artifact-panel execution-panel">
            <div className="section-label">Root alert and evidence</div>
            <h3>{latestAlertCode ? latestAlertCode : 'No latest alert code'}</h3>
            <dl className="metric-list compact">
              <MetricRow label="Root corridor alert" value={alertStatus} tone={alertTone} />
              <MetricRow label="Alert count" value={fmt(alerts.length)} tone={alerts.length ? 'tone-negative' : 'tone-positive'} />
              <MetricRow label="Total sessions" value={fmt(health.total_sessions)} />
              <MetricRow label="Latest artifact path" value={truncate(latestArtifactPath ?? '', 72)} />
            </dl>
          </section>

          <AlertListPanel alerts={alerts} setCopyStatus={setCopyStatus} />

          <section className="artifact-panel execution-panel">
            <div className="section-label">Safe review actions</div>
            <h3>Open evidence without changing state</h3>
            <div className="workflow-actions execution-actions">
              <button
                className="ghost-btn"
                type="button"
                disabled={!latestSessionDir}
                onClick={() => latestSessionDir && window.quantlabDesktop?.openPath?.(latestSessionDir)}
              >
                Open latest session
              </button>
              <button
                className="ghost-btn"
                type="button"
                disabled={!latestArtifactPath}
                onClick={() => latestArtifactPath && window.quantlabDesktop?.openPath?.(latestArtifactPath)}
              >
                Open latest artifact
              </button>
              <button
                className="ghost-btn"
                type="button"
                disabled={!surface?.submit_sessions_root}
                onClick={() => surface?.submit_sessions_root && window.quantlabDesktop?.openPath?.(surface.submit_sessions_root)}
              >
                Open submit root
              </button>
              <button
                className="ghost-btn"
                type="button"
                onClick={() => window.quantlabDesktop?.openPath?.('docs/supervised-broker-runbook.md')}
              >
                Open runbook
              </button>
              <button
                className="ghost-btn"
                type="button"
                disabled={!latestArtifactPath || typeof navigator?.clipboard?.writeText !== 'function'}
                onClick={async () => {
                  if (!latestArtifactPath || typeof navigator?.clipboard?.writeText !== 'function') return;
                  copyText(latestArtifactPath, setCopyStatus, 'Copied latest artifact path');
                }}
              >
                Copy artifact path
              </button>
            </div>
            {copyStatus && <div className="artifact-meta">{copyStatus}</div>}
          </section>

          <ArtifactListPanel artifacts={latestArtifacts} setCopyStatus={setCopyStatus} />

          <section className="artifact-panel execution-panel execution-boundary">
            <div className="section-label">Boundary</div>
            <h3>Read-only operator surface</h3>
            <p>
              Execution decisions, signing, submission gates, risk checks, and venue interaction remain outside Desktop.
              This surface elevates the evidence state only.
            </p>
          </section>
        </div>
      )}
    </div>
  );
}
