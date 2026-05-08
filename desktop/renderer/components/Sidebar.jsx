import React from 'react';
import {
  Activity,
  ShieldCheck,
  FlaskConical,
  Rocket,
  BarChart2,
  Star,
  GitCompare,
  ClipboardCheck,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';
import { useQuantLab } from './QuantLabContext';

const NAV_ICON_SIZE = 16;

function corridorChip(surface) {
  if (!surface || !surface.available) {
    return { label: 'No sessions', cls: '' };
  }
  if (surface.submit_has_alerts || surface.submit_alert_status !== 'ok') {
    return { label: 'Alert', cls: 'down' };
  }
  return { label: 'ok', cls: 'up' };
}

/**
 * Sidebar - Left navigation sidebar with:
 * - Brand mark and title
 * - Navigation items (System, Experiments, Launch, Runs, etc.)
 * - Current principle panel
 * - Runtime status
 *
 * Maps navigation actions to surface routing.
 */
export default function Sidebar({ currentSurface, isCollapsed, onToggle }) {
  const { navigateToSurface, state, getRuns, getLatestRun, decision } = useQuantLab();
  const hyperliquidSurface = state?.snapshot?.hyperliquidSurface ?? null;
  const corridor = corridorChip(hyperliquidSurface);

  const navItems = [
    { id: 'system',      label: 'System',      Icon: Activity       },
    { id: 'execution',   label: 'Execution',   Icon: ShieldCheck    },
    { id: 'experiments', label: 'Experiments', Icon: FlaskConical   },
    { id: 'launch',      label: 'Launch',      Icon: Rocket         },
    { id: 'runs',        label: 'Runs',        Icon: BarChart2      },
    { id: 'candidates',  label: 'Candidates',  Icon: Star           },
    { id: 'compare',     label: 'Compare',     Icon: GitCompare     },
    { id: 'paper-ops',   label: 'Paper Ops',   Icon: ClipboardCheck },
    { id: 'assistant',   label: 'Assistant',   Icon: MessageSquare  },
  ];

  // Contextual data for surface panels
  const runs = getRuns?.() ?? [];
  const latestRun = getLatestRun?.();
  const candidateEntries = decision?.getCandidateEntriesResolved?.() ?? [];
  const shortlistCount = candidateEntries.filter((e) => e.shortlisted && e.run).length;
  const baselineId = state?.candidatesStore?.baseline_run_id ?? null;
  const paper = state?.snapshot?.paperHealth ?? null;
  const launchJobs = state?.snapshot?.launchControl?.jobs ?? [];
  const latestJob = launchJobs[0] ?? null;

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Toggle — always visible, anchored to top */}
      <button
        className="sidebar-toggle-btn"
        onClick={onToggle}
        aria-label={isCollapsed ? 'Open sidebar' : 'Close sidebar'}
        title={isCollapsed ? 'Open sidebar' : 'Close sidebar'}
      >
        {isCollapsed
          ? <PanelLeftOpen size={18} strokeWidth={1.6} />
          : <PanelLeftClose size={18} strokeWidth={1.6} />
        }
      </button>

      {!isCollapsed && (
        <>
          {/* Brand Section */}
          <div className="sidebar-brand">
            <div className="brand-mark" aria-hidden="true">
              <span className="brand-mark-ring"></span>
              <span className="brand-mark-tail"></span>
              <span className="brand-mark-grid">
                <span></span>
                <span></span>
                <span></span>
                <span></span>
              </span>
              <span className="brand-mark-core"></span>
            </div>
            <div>
              <div className="brand-title">QuantLab Desktop</div>
              <div className="brand-subtitle">Research workstation</div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="sidebar-nav">
            {navItems.map(({ id, label, Icon }) => (
              <button
                key={id}
                className={`nav-item ${currentSurface === id ? 'is-active' : ''}`}
                onClick={() => navigateToSurface(id)}
                title={label}
                data-action={`open-${id}`}
              >
                <span className="nav-icon" aria-hidden="true">
                  <Icon size={NAV_ICON_SIZE} strokeWidth={1.75} />
                </span>
                <span className="nav-label">{label}</span>
              </button>
            ))}
          </nav>

          {/* Support Panels */}
          <div className="sidebar-panels">
            <ContextPanel
              surface={currentSurface}
              runs={runs}
              latestRun={latestRun}
              shortlistCount={shortlistCount}
              baselineId={baselineId}
              paper={paper}
              latestJob={latestJob}
              corridor={corridor}
            />
            <section className="sidebar-panel">
              <div className="panel-label">Runtime</div>
              <div className="runtime-chip">
                <span className="chip-indicator">●</span>
                <span className="chip-text">Ready</span>
              </div>
            </section>
            <section className="sidebar-panel">
              <div className="panel-label">Corridor</div>
              <div className={`runtime-chip ${corridor.cls}`}>
                <span className="chip-indicator">●</span>
                <span className="chip-text">{corridor.label}</span>
              </div>
            </section>
          </div>
        </>
      )}
    </aside>
  );
}

function ContextPanel({ surface, runs, latestRun, shortlistCount, baselineId, paper, latestJob, corridor }) {
  switch (surface) {
    case 'runs':
      return (
        <section className="sidebar-panel">
          <div className="panel-label">At a glance</div>
          <div className="sidebar-context-list">
            <div className="sidebar-context-row">
              <span>Indexed</span><strong>{runs.length}</strong>
            </div>
            <div className="sidebar-context-row">
              <span>Shortlisted</span><strong>{shortlistCount}</strong>
            </div>
            <div className="sidebar-context-row">
              <span>Baseline</span><strong>{baselineId ?? '—'}</strong>
            </div>
            {latestRun && (
              <div className="sidebar-context-row">
                <span>Latest</span><strong title={latestRun.run_id}>{String(latestRun.run_id).slice(-8)}</strong>
              </div>
            )}
          </div>
        </section>
      );

    case 'launch':
      return (
        <section className="sidebar-panel">
          <div className="panel-label">At a glance</div>
          <div className="sidebar-context-list">
            {latestJob ? (
              <>
                <div className="sidebar-context-row">
                  <span>Latest job</span><strong>{latestJob.command ?? '—'}</strong>
                </div>
                <div className="sidebar-context-row">
                  <span>Status</span><strong>{latestJob.status ?? '—'}</strong>
                </div>
              </>
            ) : (
              <div className="sidebar-context-row">
                <span>Jobs</span><strong>None yet</strong>
              </div>
            )}
          </div>
        </section>
      );

    case 'candidates':
    case 'compare':
      return (
        <section className="sidebar-panel">
          <div className="panel-label">At a glance</div>
          <div className="sidebar-context-list">
            <div className="sidebar-context-row">
              <span>Shortlisted</span><strong>{shortlistCount}</strong>
            </div>
            <div className="sidebar-context-row">
              <span>Baseline</span><strong>{baselineId ?? '—'}</strong>
            </div>
          </div>
        </section>
      );

    case 'paper-ops':
      return (
        <section className="sidebar-panel">
          <div className="panel-label">At a glance</div>
          <div className="sidebar-context-list">
            <div className="sidebar-context-row">
              <span>Paper state</span>
              <strong>{paper?.available ? 'Ready' : 'Pending'}</strong>
            </div>
          </div>
        </section>
      );

    case 'system':
    case 'execution':
      return (
        <section className="sidebar-panel">
          <div className="panel-label">At a glance</div>
          <div className="sidebar-context-list">
            <div className="sidebar-context-row">
              <span>Corridor</span>
              <strong className={corridor.cls === 'up' ? 'tone-positive' : corridor.cls === 'down' ? 'tone-negative' : ''}>
                {corridor.label}
              </strong>
            </div>
            <div className="sidebar-context-row">
              <span>Indexed runs</span><strong>{runs.length}</strong>
            </div>
          </div>
        </section>
      );

    default:
      return (
        <section className="sidebar-panel">
          <div className="panel-label">Current principle</div>
          <p>One shell, one runtime strip, one place to launch, inspect, compare, and decide.</p>
        </section>
      );
  }
}
