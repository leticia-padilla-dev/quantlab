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
      label: 'Unavailable',
      cls: 'muted',
    };
  }
  const health = surface.submit_health || {};
  const rootAlert = surface.submit_alert_status || 'unknown';
  const sessions = Number(health.total_sessions || 0);
  const hasAlerts = Boolean(surface.submit_has_alerts) || rootAlert !== 'ok';
  const cls = hasAlerts ? 'warn' : 'up';
  const label = hasAlerts ? 'Alerts' : 'OK';

  return {
    label: `${label} · ${sessions}`,
    cls,
  };
}

function workspaceChip(workspace) {
  const status = String(workspace?.status || 'idle').toLowerCase();
  if (status === 'ready') return { label: 'Workspace: online', cls: 'up' };
  if (status === 'starting') return { label: 'Workspace: starting', cls: 'muted' };
  if (status === 'stopped') return { label: 'Workspace: offline', cls: 'muted' };
  if (status === 'error') return { label: 'Workspace: degraded', cls: 'warn' };
  return { label: 'Workspace: idle', cls: 'muted' };
}

function registryChip({ registryLoading, registryError, runsCount }) {
  if (registryLoading) return { label: `Runs: ${runsCount} · loading`, cls: 'muted' };
  if (registryError) return { label: `Runs: ${runsCount} · error`, cls: 'warn' };
  return { label: `Runs: ${runsCount}`, cls: 'up' };
}

function paperChip(paperHealth) {
  if (!paperHealth) return { label: 'Paper: —', cls: 'muted' };
  const total = Number(paperHealth.total_sessions || 0);
  const active = Array.isArray(paperHealth.active_sessions) ? paperHealth.active_sessions.length : 0;
  const label = active ? `Paper: ${total} sessions · ${active} active` : `Paper: ${total} sessions`;
  return { label, cls: 'muted' };
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
