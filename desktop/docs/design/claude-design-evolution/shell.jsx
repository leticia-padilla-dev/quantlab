// QuantLab Desktop — Evolved shell
// Sidebar nav + status strip + tabs + body. Surface routing via React state.

const { useState, useMemo, useEffect } = React;
// RUNS, ARTIFACTS, CONFIG_DELTAS, PAPER_SESSIONS, CORRIDOR are globals from data.jsx

// ── helpers ──────────────────────────────────────────────
const fmtPct = (v) => v == null ? "—" : `${(v*100).toFixed(2)}%`;
const fmtNum = (v, d=2) => v == null ? "—" : Number(v).toFixed(d);
const tone = (v, higherBetter=true) => {
  if (v == null) return "";
  if (higherBetter) return v >= 0 ? "tone-positive" : "tone-negative";
  return v <= -0.10 ? "tone-negative" : v <= -0.05 ? "tone-warning" : "tone-positive";
};
const shortId = (id) => id.length > 18 ? id.slice(0, 9) + "…" + id.slice(-6) : id;

// ── Icons (line, 14px, no fill) ─────────────────────────
const Icon = ({ d, size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none"
    stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);
const ICONS = {
  system:      "M2 8h2l2-5 4 10 2-5h2",
  execution:   "M3 3.5h10v9H3zM3 7h10M6 10h4",
  experiments: "M6 2v4l-3 7c-.5 1 .2 2 1.3 2h7.4c1.1 0 1.8-1 1.3-2l-3-7V2zM5 2h6",
  launch:      "M8 12V4M4 8l4-4 4 4M3 13.5h10",
  runs:        "M2.5 13.5V8M6.5 13.5V4.5M10.5 13.5V10M14 13.5V6",
  candidates:  "M8 2.5l1.7 3.5 3.8.5-2.8 2.7.7 3.8L8 11.2 4.6 13l.7-3.8L2.5 6.5l3.8-.5z",
  compare:     "M3.5 4.5h4M3.5 8h4M3.5 11.5h4M8.5 4.5h4M8.5 8h4M8.5 11.5h4M8 2v12",
  paper:       "M3 2.5h7l3 3v8H3zM10 2.5v3h3M5 9h6M5 11h4",
  assistant:   "M3 3.5h10v7H8l-3 2.5v-2.5H3z",
  refresh:     "M13 8a5 5 0 1 1-1.5-3.5L13 6M13 3v3h-3",
  search:      "M7 12.5A5.5 5.5 0 1 0 7 1.5a5.5 5.5 0 0 0 0 11zM11 11l3 3",
  download:    "M8 2v8M4.5 7.5L8 11l3.5-3.5M3 13.5h10",
  close:       "M3.5 3.5l9 9M12.5 3.5l-9 9",
  star:        "M8 2.5l1.7 3.5 3.8.5-2.8 2.7.7 3.8L8 11.2 4.6 13l.7-3.8L2.5 6.5l3.8-.5z",
  chevR:       "M6 3.5l4 4.5-4 4.5",
};

// ── Sidebar ─────────────────────────────────────────────
const NAV = [
  { group: "Operations", items: [
    { id: "system",      label: "System",      icon: "system",      count: null },
    { id: "execution",   label: "Execution",   icon: "execution",   count: "3" },
    { id: "paper",       label: "Paper Ops",   icon: "paper",       count: "3" },
  ]},
  { group: "Research",   items: [
    { id: "experiments", label: "Experiments", icon: "experiments", count: "12" },
    { id: "launch",      label: "Launch",      icon: "launch",      count: null },
    { id: "runs",        label: "Runs",        icon: "runs",        count: "8" },
  ]},
  { group: "Decision",   items: [
    { id: "candidates",  label: "Candidates",  icon: "candidates",  count: "5" },
    { id: "compare",     label: "Compare",     icon: "compare",     count: null },
  ]},
  { group: "Support",    items: [
    { id: "assistant",   label: "Assistant",   icon: "assistant",   count: null },
  ]},
];

function Sidebar({ surface, onNav }) {
  const corr = CORRIDOR;
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark" aria-hidden="true"></div>
        <div>
          <div className="brand-title">QuantLab Desktop</div>
          <div className="brand-sub">RESEARCH · WORKSTATION</div>
        </div>
      </div>

      {NAV.map((grp) => (
        <div key={grp.group} className="nav-group">
          <div className="nav-group-label">{grp.group}</div>
          {grp.items.map((it) => (
            <button
              key={it.id}
              className={`nav-item ${surface === it.id ? "active" : ""}`}
              onClick={() => onNav(it.id)}>
              <span className="nav-glyph"><Icon d={ICONS[it.icon]} /></span>
              <span>{it.label}</span>
              {it.count && <span className="nav-count">{it.count}</span>}
            </button>
          ))}
        </div>
      ))}

      <div className="sidebar-context">
        <div className="sb-card">
          <div className="eyebrow" style={{ marginBottom: 6 }}>Corridor · last {corr.last_check}</div>
          <div className="sb-row"><span>Root alert</span><strong className="tone-positive">OK</strong></div>
          <div className="sb-row"><span>Sessions</span><strong>{corr.sessions}</strong></div>
          <div className="sb-row"><span>Latest submit</span><strong>{corr.latest_submit}</strong></div>
        </div>
        <div className="sb-card">
          <div className="eyebrow" style={{ marginBottom: 6 }}>Build</div>
          <div className="sb-row"><span>v0.14.2</span><strong className="mono">a91f3c2</strong></div>
        </div>
      </div>
    </aside>
  );
}

// ── Status strip + Topbar ───────────────────────────────
function StatusStrip() {
  return (
    <div className="status-strip">
      <div className="status-cell">
        <span className="status-dot ok"></span>
        <span className="status-label">Runtime</span>
        <span className="status-value">Ready</span>
      </div>
      <div className="status-cell">
        <span className="status-dot ok"></span>
        <span className="status-label">Corridor</span>
        <span className="status-value">OK · 3 sessions · signed</span>
      </div>
      <div className="status-cell">
        <span className="status-dot ok"></span>
        <span className="status-label">Reachability</span>
        <span className="status-value">research_ui · 12s</span>
      </div>
      <div className="status-cell">
        <span className="status-dot ok"></span>
        <span className="status-label">Index</span>
        <span className="status-value">8 runs · 5 candidates · 1 baseline</span>
      </div>
      <div className="status-cell">
        <span className="status-label">Local</span>
        <span className="status-value">~/quantlab/outputs</span>
      </div>
    </div>
  );
}

const SURFACE_META = {
  system:      { crumb: "Operations / System",       title: "System" },
  execution:   { crumb: "Operations / Execution",    title: "Execution" },
  paper:       { crumb: "Operations / Paper Ops",    title: "Paper Operations" },
  experiments: { crumb: "Research / Experiments",    title: "Experiments" },
  launch:      { crumb: "Research / Launch",         title: "Launch" },
  runs:        { crumb: "Research / Runs",           title: "Runs" },
  candidates:  { crumb: "Decision / Candidates",     title: "Candidates" },
  compare:     { crumb: "Decision / Compare",        title: "Compare" },
  assistant:   { crumb: "Support / Assistant",       title: "Assistant" },
  "run-detail":{ crumb: "Research / Runs / Detail",  title: "Run Detail" },
};

function Topbar({ surface, onAction }) {
  const m = SURFACE_META[surface] || { crumb: "—", title: "—" };
  return (
    <div className="topbar">
      <div>
        <div className="topbar-crumb">{m.crumb}</div>
        <h1>{m.title}</h1>
      </div>
      <div className="topbar-actions">
        <button className="btn" onClick={() => onAction?.("refresh")}>
          <Icon d={ICONS.refresh} /> Refresh
        </button>
        <button className="btn primary" onClick={() => onAction?.("launch")}>
          <Icon d={ICONS.launch} /> Launch run
        </button>
      </div>
    </div>
  );
}

// ── Tab bar ─────────────────────────────────────────────
function TabBar({ tabs, activeId, onActivate, onClose }) {
  return (
    <div className="tabs">
      {tabs.map((t) => (
        <button
          key={t.id}
          className={`tab ${activeId === t.id ? "active" : ""}`}
          onClick={() => onActivate(t.id)}>
          <span className="tab-kind">{t.kind}</span>
          <span>{t.title}</span>
          {t.closable !== false && (
            <span className="tab-close" onClick={(e) => { e.stopPropagation(); onClose(t.id); }}>×</span>
          )}
        </button>
      ))}
    </div>
  );
}

Object.assign(window, {
  Icon, ICONS,
  fmtPct, fmtNum, tone, shortId,
  Sidebar, StatusStrip, Topbar, TabBar, SURFACE_META,
});
