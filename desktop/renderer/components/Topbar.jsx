import React from 'react';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useQuantLab } from './QuantLabContext';

/**
 * Topbar - Top navigation bar with:
 * - Runtime status indicator
 * - Version display
 * - Sidebar toggle
 *
 * This is the minimal topbar for the new shell frame.
 * It provides visibility into system state without replacing legacy surfaces.
 */
function corridorChip(surface) {
  if (!surface || !surface.available) {
    return {
      label: 'No sessions',
      cls: 'muted',
    };
  }
  const health = surface.submit_health || {};
  const rootAlert = surface.submit_alert_status || 'unknown';
  const sessions = Number(health.total_sessions || 0);
  const rootAlertLabel = rootAlert === 'ok'
    ? 'OK'
    : rootAlert.charAt(0).toUpperCase() + rootAlert.slice(1);
  const cls = surface.submit_has_alerts || rootAlert !== 'ok'
    ? 'down'
    : 'up';

  return {
    label: `${rootAlertLabel} · ${sessions} session${sessions === 1 ? '' : 's'}`,
    cls,
  };
}

function workspaceChip(workspace) {
  const status = String(workspace?.status || 'idle').toLowerCase();
  if (status === 'ready') return { label: 'API: ready', cls: 'up' };
  if (status === 'starting') return { label: 'API: starting', cls: 'warn' };
  if (status === 'stopped') return { label: 'API: stopped', cls: 'down' };
  if (status === 'error') return { label: 'API: error', cls: 'down' };
  return { label: 'API: idle', cls: 'muted' };
}

function registryChip({ registryLoading, registryError, runsCount }) {
  if (registryLoading) return { label: `Runs: ${runsCount} · loading`, cls: 'muted' };
  if (registryError) return { label: `Runs: ${runsCount} · error`, cls: 'warn' };
  return { label: `Runs: ${runsCount}`, cls: 'up' };
}

function paperChip(paperHealth) {
  if (!paperHealth) return { label: 'Paper: —', cls: 'muted' };
  const total = Number(paperHealth.total_sessions || 0);
  const latest = paperHealth.latest_session_status || '—';
  const issue = String(paperHealth.latest_issue_status || '').toLowerCase();
  if (issue === 'failed') return { label: `Paper: ${total} · ${latest}`, cls: 'down' };
  if (issue === 'aborted' || issue === 'running') return { label: `Paper: ${total} · ${latest}`, cls: 'warn' };
  return { label: `Paper: ${total} · ${latest}`, cls: 'up' };
}

function formatSurfaceLabel(surface) {
  const labels = {
    'system': 'System',
    'experiments': 'Experiments',
    'launch': 'Launch',
    'runs': 'Runs',
    'candidates': 'Candidates',
    'compare': 'Compare',
    'paper-ops': 'Paper Ops',
    'assistant': 'Assistant',
  };
  return labels[surface] || surface;
}

export default function Topbar({ currentSurface, onToggleSidebar, isSidebarCollapsed }) {
  const { state, getRuns } = useQuantLab();
  const [workspace, setWorkspace] = React.useState(null);

  React.useEffect(() => {
    const bridge = window.quantlabDesktop;
    let unsubscribe = null;

    async function load() {
      if (typeof bridge?.getWorkspaceState === 'function') {
        try {
          const next = await bridge.getWorkspaceState();
          setWorkspace(next || null);
        } catch (_err) {
          setWorkspace(null);
        }
      }
    }

    load();

    if (typeof bridge?.onWorkspaceState === 'function') {
      unsubscribe = bridge.onWorkspaceState((next) => {
        setWorkspace(next || null);
      });
    }

    return () => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, []);

  const hyperliquidSurface = state?.snapshot?.hyperliquidSurface ?? null;
  const corridor = corridorChip(hyperliquidSurface);
  const runtime = workspaceChip(workspace);
  const runsCount = Number((getRuns?.() || []).length);
  const runs = registryChip({
    registryLoading: state?.registryLoading,
    registryError: state?.registryError,
    runsCount,
  });
  const paper = paperChip(state?.snapshot?.paperHealth ?? null);

  return (
    <header className="topbar status-strip">
      <button
        className="topbar-toggle"
        onClick={onToggleSidebar}
        aria-label={isSidebarCollapsed ? 'Open sidebar' : 'Close sidebar'}
        title={isSidebarCollapsed ? 'Open sidebar' : 'Close sidebar'}
      >
        {isSidebarCollapsed
          ? <PanelLeftOpen size={18} strokeWidth={1.6} />
          : <PanelLeftClose size={18} strokeWidth={1.6} />
        }
      </button>

      <div className="status-strip-title">
        <span className="status-strip-product">QuantLab Desktop</span>
        <span className="status-strip-surface">{formatSurfaceLabel(currentSurface)}</span>
      </div>

      <div className="topbar-status-row status-strip-chips">
        <span className={`topbar-status-chip ${runtime.cls}`}>{runtime.label}</span>
        <span className={`topbar-status-chip ${corridor.cls}`}>Corridor: {corridor.label}</span>
        <span className={`topbar-status-chip ${paper.cls}`}>{paper.label}</span>
        <span className={`topbar-status-chip ${runs.cls}`}>{runs.label}</span>
      </div>
    </header>
  );
}
