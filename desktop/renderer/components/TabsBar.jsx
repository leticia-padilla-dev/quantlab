import React from 'react';
import { useQuantLab } from './QuantLabContext';
import './TabsBar.css';

const SURFACE_LABELS = {
  system: 'System',
  experiments: 'Experiments',
  launch: 'Launch',
  runs: 'Runs',
  candidates: 'Candidates',
  compare: 'Compare',
  execution: 'Execution',
  'paper-ops': 'Paper Ops',
  assistant: 'Assistant',
};

/**
 * TabsBar - Workspace tab navigation bar.
 * Includes surface label + Ready status on the right.
 */
export function TabsBar() {
  const { state, setActiveTab, closeTab } = useQuantLab();
  const tabs = state.tabs || [];
  const activeTabId = state.activeTabId;
  const activeTab = tabs.find((t) => t.id === activeTabId) || null;
  const surfaceLabel = SURFACE_LABELS[activeTab?.navKind || activeTab?.kind] || '';

  if (tabs.length === 0) {
    return null;
  }

  return (
    <div id="tabs-bar" className="tabs-bar">
      <div className="tabs-bar-pills">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-pill ${tab.id === activeTabId ? 'is-active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            type="button"
            data-tab-id={tab.id}
          >
            <span>{tab.title}</span>
            <span
              className="tab-close"
              onClick={(e) => {
                e.stopPropagation();
                closeTab(tab.id);
              }}
              data-close-tab={tab.id}
            >
              ×
            </span>
          </button>
        ))}
      </div>
      <div className="tabs-bar-status">
        {surfaceLabel && <span className="tabs-surface-label">{surfaceLabel.toUpperCase()}</span>}
        <div className="tabs-runtime-indicator">
          <span className="indicator-dot online" aria-hidden="true"></span>
          <span className="indicator-label">Ready</span>
        </div>
      </div>
    </div>
  );
}
