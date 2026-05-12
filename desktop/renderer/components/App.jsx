import React, { useState } from 'react';
import Sidebar from './Sidebar.jsx';
import MainContent from './MainContent.jsx';
import {
  QuantLabContextProvider,
  useQuantLabContextValue,
  RegistryProvider,
} from './QuantLabContext.jsx';
import { getQuantLabContextContractIssues } from '../modules/quantlab-context-contract.js';

/**
 * AppShell — inner shell component.
 * Lives inside RegistryProvider so useQuantLabContextValue can call useRegistry().
 */
function AppShell() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Build the full context value (must be called unconditionally before any early return)
  const contextValue = useQuantLabContextValue();

  React.useEffect(() => {
    if (!window.__quantlab) {
      window.__quantlab = { rendererMode: 'react' };
    } else {
      window.__quantlab.rendererMode = 'react';
    }
    window.__quantlab.getShellState = () => ({
      rendererMode: 'react',
      reactRoot: document.getElementById('react-root'),
      legacyShell: document.getElementById('legacy-shell'),
      currentSurface: window.__quantlab?.currentSurface || 'runs',
    });
  }, []);

  const allTabs = contextValue.state?.tabs || [];
  const activeTabId = contextValue.state?.activeTabId || null;
  const activeTab = allTabs.find((t) => t.id === activeTabId) || null;
  const hasActiveTabMismatch = Boolean(
    contextValue.state?.isInitialized
    && activeTabId
    && !activeTab
  );
  const currentSurface = activeTab?.navKind || activeTab?.kind || 'system';

  // Expose metadata for smoke tests; kept in an effect to avoid conditional hook calls
  React.useEffect(() => {
    if (!window.__quantlab) return;
    window.__quantlab.currentSurface = currentSurface;
  }, [currentSurface]);

  const contractIssues = getQuantLabContextContractIssues(contextValue);
  if (contractIssues.length) {
    return (
      <div className="app-container loading">
        <div className="loading-message" data-smoke="shell-contract-mismatch">
          <div className="section-label">Shell contract mismatch</div>
          <p>QuantLabContext is missing required contract fields.</p>
          <div className="artifact-meta">{contractIssues.join(', ')}</div>
        </div>
      </div>
    );
  }

  // Loading guard — safe here because all hooks have already been called
  if (!contextValue?.state || !contextValue.state.isInitialized) {
    return (
      <div className="app-container loading">
        <div className="loading-message">
          <div className="spinner"></div>
          <p>QuantLab Desktop is initializing...</p>
        </div>
      </div>
    );
  }

  const handleToggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleTabChange = (tabId) => {
    contextValue.setActiveTab(tabId);
  };

  return (
    <QuantLabContextProvider value={contextValue}>
      <div className={`app-container ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`} data-smoke="react-shell">
        <Sidebar
          currentSurface={currentSurface}
          isCollapsed={isSidebarCollapsed}
          onToggle={handleToggleSidebar}
        />

        <MainContent
          activeTab={activeTab}
          allTabs={allTabs}
          onTabChange={handleTabChange}
          shellStateMismatch={hasActiveTabMismatch ? {
            activeTabId,
          } : null}
        />
      </div>
    </QuantLabContextProvider>
  );
}

export default function App() {
  return (
    <RegistryProvider>
      <AppShell />
    </RegistryProvider>
  );
}
