import React from 'react';
import {
  Activity,
  FlaskConical,
  Rocket,
  BarChart2,
  Star,
  GitCompare,
  ClipboardCheck,
  MessageSquare,
} from 'lucide-react';
import { useQuantLab } from './QuantLabContext';

const NAV_ICON_SIZE = 16;

/**
 * Sidebar - Left navigation sidebar with:
 * - Brand mark and title
 * - Navigation items (System, Experiments, Launch, Runs, etc.)
 * - Current principle panel
 * - Runtime status
 *
 * Maps navigation actions to surface routing.
 */
export default function Sidebar({ currentSurface, isCollapsed }) {
  const { navigateToSurface } = useQuantLab();

  const navItems = [
    { id: 'system',      label: 'System',      Icon: Activity       },
    { id: 'experiments', label: 'Experiments', Icon: FlaskConical   },
    { id: 'launch',      label: 'Launch',      Icon: Rocket         },
    { id: 'runs',        label: 'Runs',        Icon: BarChart2      },
    { id: 'candidates',  label: 'Candidates',  Icon: Star           },
    { id: 'compare',     label: 'Compare',     Icon: GitCompare     },
    { id: 'paper-ops',   label: 'Paper Ops',   Icon: ClipboardCheck },
    { id: 'assistant',   label: 'Assistant',   Icon: MessageSquare  },
  ];

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
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
            <section className="sidebar-panel">
              <div className="panel-label">Current principle</div>
              <p>One shell, one runtime strip, one place to launch, inspect, compare, and decide.</p>
            </section>

            <section className="sidebar-panel">
              <div className="panel-label">Runtime</div>
              <div className="runtime-chip">
                <span className="chip-indicator">●</span>
                <span className="chip-text">Ready</span>
              </div>
            </section>
          </div>
        </>
      )}
    </aside>
  );
}
