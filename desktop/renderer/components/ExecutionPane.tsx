import React from 'react';
import type { ExecutionTab } from '../../shared/models/tab';
import type { SnapshotStatus } from '../../shared/models/snapshot';
import { useSnapshot } from '../hooks/useSnapshot.js';
import { useQuantLab as _useQuantLab } from './QuantLabContext';

// QuantLabContext is a JS file; cast to any so strict-mode TSX can consume it.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const useQuantLab = _useQuantLab as () => any;

const DEFAULT_RESEARCH_UI_SERVER_URL = 'http://127.0.0.1:8000';

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

export function ExecutionPane({ tab: _tab }: { tab: ExecutionTab }) {
  const { state } = useQuantLab();
  const workspace = state.workspace ?? {};
  const workspaceServerUrl = typeof workspace.serverUrl === 'string' ? workspace.serverUrl.trim() : '';
  const native = useSnapshot(state.snapshot != null ? null : (workspaceServerUrl || DEFAULT_RESEARCH_UI_SERVER_URL));
  const snapshotStatus: Partial<SnapshotStatus> = state.snapshotStatus ?? native.snapshotStatus ?? {};
  const snapshot = state.snapshot ?? native.snapshot ?? {};
  const surface = (snapshot as any).hyperliquidSurface ?? null;

  const empty = !surface || !surface.available;
  const health = surface?.submit_health ?? {};
  const alerts: any[] = Array.isArray(surface?.submit_alerts) ? surface.submit_alerts : [];
  const latestAlertCode: string | null = alerts[0]?.code ?? null;
  const alertStatus: string = surface?.submit_alert_status ?? 'unknown';
  const latestArtifact: any =
    surface?.latest_artifacts?.order_status ??
    surface?.latest_artifacts?.submit_response ??
    surface?.latest_artifacts?.continuous_supervision ??
    null;
  const latestArtifactPath: string | null = latestArtifact?.path ?? null;
  const latestUpdatedAt: string | null = surface?.latest_ready_generated_at ?? health.latest_submit_at ?? null;
  const signatureState: string = surface?.signature_state ?? 'unknown';
  const latestSubmitState: string = health.latest_submit_state ?? 'unknown';
  const latestOrderState: string = health.latest_order_state ?? 'unknown';
  const latestArtifactState: string = latestArtifact?.normalized_state ?? 'unknown';
  const alertTone = empty ? 'tone-warning' : statusTone(alertStatus);
  const snapshotLabel = snapshotStatus.status === 'ok'
    ? 'Live'
    : snapshotStatus.status === 'degraded'
      ? 'Degraded'
      : snapshotStatus.status === 'error'
        ? 'Unavailable'
        : 'Waiting';

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
          <span>Alert status</span>
          <strong>{empty ? 'Unavailable' : titleCase(alertStatus)}</strong>
        </div>
      </div>

      <div className="tab-summary-grid">
        <SummaryCard label="Total sessions" value={fmt(health.total_sessions)} tone={empty ? 'tone-warning' : 'tone-positive'} />
        <SummaryCard label="Latest submit" value={titleCase(latestSubmitState)} tone={statusTone(latestSubmitState)} />
        <SummaryCard label="Latest order" value={titleCase(latestOrderState)} tone={statusTone(latestOrderState)} />
        <SummaryCard label="Artifact state" value={titleCase(latestArtifactState)} tone={statusTone(latestArtifactState)} />
        <SummaryCard label="Signature" value={titleCase(signatureState)} tone={statusTone(signatureState)} />
        <SummaryCard label="Snapshot" value={snapshotLabel} tone={snapshotStatus.status === 'ok' ? 'tone-positive' : 'tone-warning'} />
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
            <div className="section-label">Latest session</div>
            <h3>{health.latest_submit_session_id ?? 'No session id'}</h3>
            <dl className="metric-list compact">
              <MetricRow label="Submit state" value={latestSubmitState} tone={statusTone(latestSubmitState)} />
              <MetricRow label="Order state" value={latestOrderState} tone={statusTone(latestOrderState)} />
              <MetricRow label="Artifact state" value={latestArtifactState} tone={statusTone(latestArtifactState)} />
              <MetricRow label="Signature state" value={signatureState} tone={statusTone(signatureState)} />
              <MetricRow label="Last evidence at" value={fmtDate(latestUpdatedAt)} />
            </dl>
          </section>

          <section className="artifact-panel execution-panel">
            <div className="section-label">Alerts and evidence</div>
            <h3>{latestAlertCode ? latestAlertCode : 'No latest alert code'}</h3>
            <dl className="metric-list compact">
              <MetricRow label="Alert status" value={alertStatus} tone={alertTone} />
              <MetricRow label="Alert count" value={fmt(alerts.length)} tone={alerts.length ? 'tone-negative' : 'tone-positive'} />
              <MetricRow label="Latest artifact path" value={truncate(latestArtifactPath ?? '', 72)} />
            </dl>
          </section>

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
