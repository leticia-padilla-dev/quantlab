import React from 'react';

export function AssistantPane({ tab: _tab }) {
  return (
    <div className="tab-shell assistant-pane" data-smoke="surface-assistant">
      <section className="surface-section">
        <div className="section-label">Assistant</div>
        <h2>Assistant surface unavailable</h2>
        <p>
          External assistant integrations have been removed from Desktop. QuantLab
          remains available through the native operator surfaces: System, Launch,
          Runs, Candidates, Compare, and Paper Ops.
        </p>
        <p>
          Future assistant work must be explicitly QuantLab-owned and must not
          reintroduce an external workspace dependency through Desktop.
        </p>
      </section>
    </div>
  );
}
