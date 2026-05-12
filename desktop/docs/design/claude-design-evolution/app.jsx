// QuantLab Desktop — App root + Tweaks
const { useState: uS, useEffect: uE } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "density": "default",
  "accent": "#62d4ff",
  "gridlines": "on",
  "monoFont": "JetBrains Mono"
}/*EDITMODE-END*/;

const ACCENT_MAP = {
  "#62d4ff": { line: "rgba(98,212,255,0.45)",  soft: "rgba(98,212,255,0.12)"  },
  "#7fa6ff": { line: "rgba(127,166,255,0.45)", soft: "rgba(127,166,255,0.14)" },
  "#9ec5d9": { line: "rgba(158,197,217,0.45)", soft: "rgba(158,197,217,0.14)" },
  "#a8e2c2": { line: "rgba(168,226,194,0.45)", soft: "rgba(168,226,194,0.14)" },
};

function App() {
  const [t, setT] = window.useTweaks(TWEAK_DEFAULTS);
  const [surface, setSurface] = uS("runs");
  const [tabs, setTabs] = uS([
    { id: "t-runs",        kind: "RUNS",    title: "Runs",                        surface: "runs",       closable: false },
    { id: "t-run-detail",  kind: "RUN",     title: "wf_2026-05-09_btc-mr_03",     surface: "run-detail", runId: "wf_2026-05-09_btc-mr_03" },
    { id: "t-compare",     kind: "COMPARE", title: "Shortlist · 3 runs",          surface: "compare" },
  ]);
  const [activeTab, setActiveTab] = uS("t-runs");
  const [openRunId, setOpenRunId] = uS("wf_2026-05-09_btc-mr_03");
  const [compareIds, setCompareIds] = uS(null);

  uE(() => {
    const r = document.documentElement;
    const a = ACCENT_MAP[t.accent] || ACCENT_MAP["#62d4ff"];
    r.style.setProperty("--accent", t.accent);
    r.style.setProperty("--accent-line", a.line);
    r.style.setProperty("--accent-soft", a.soft);
    r.setAttribute("data-density", t.density);
    r.setAttribute("data-gridlines", t.gridlines);
    r.style.setProperty("--font-mono", `"${t.monoFont}", ui-monospace, monospace`);
  }, [t]);

  const activateTab = (id) => {
    const tab = tabs.find((x) => x.id === id);
    if (!tab) return;
    setActiveTab(id);
    setSurface(tab.surface);
    if (tab.runId) setOpenRunId(tab.runId);
  };
  const closeTab = (id) => {
    const idx = tabs.findIndex((x) => x.id === id);
    const next = tabs.filter((x) => x.id !== id);
    setTabs(next);
    if (activeTab === id && next.length) {
      const fb = next[Math.max(0, idx - 1)];
      activateTab(fb.id);
    }
  };
  const navigateSurface = (s) => {
    setSurface(s);
    const existing = tabs.find((x) => x.surface === s && !x.runId);
    if (existing) { setActiveTab(existing.id); return; }
    const nt = {
      id: `t-${s}-${Date.now()}`,
      kind: (SURFACE_META[s]?.title || s).toUpperCase().slice(0, 7),
      title: SURFACE_META[s]?.title || s,
      surface: s,
    };
    setTabs([...tabs, nt]);
    setActiveTab(nt.id);
  };
  const openRun = (id) => {
    setOpenRunId(id);
    setSurface("run-detail");
    const existing = tabs.find((x) => x.runId === id);
    if (existing) { setActiveTab(existing.id); return; }
    const nt = { id: `t-run-${id}`, kind: "RUN", title: id, surface: "run-detail", runId: id };
    setTabs([...tabs, nt]);
    setActiveTab(nt.id);
  };
  const openCompare = (ids) => {
    setCompareIds(ids && ids.length >= 2 ? ids : null);
    setSurface("compare");
    const existing = tabs.find((x) => x.surface === "compare");
    if (existing) { setActiveTab(existing.id); return; }
    const nt = { id: `t-cmp-${Date.now()}`, kind: "COMPARE", title: `${ids?.length || "shortlist"} runs`, surface: "compare" };
    setTabs([...tabs, nt]);
    setActiveTab(nt.id);
  };

  return (
    <>
      <div className="app">
        <Sidebar surface={surface} onNav={navigateSurface} />
        <div className="main">
          <StatusStrip />
          <TabBar tabs={tabs} activeId={activeTab} onActivate={activateTab} onClose={closeTab} />
          <Topbar surface={surface} />
          <div className="body">
            {surface === "runs"        && <RunsSurface       onOpenRun={openRun} onCompare={openCompare} />}
            {surface === "run-detail"  && <RunDetailSurface  runId={openRunId} onBack={() => navigateSurface("runs")} onCompare={openCompare} />}
            {surface === "compare"     && <CompareSurface    runIds={compareIds} onOpenRun={openRun} />}
            {surface === "system"      && <SystemSurface     />}
            {surface === "execution"   && <StubSurface       title="Execution" note="Execution corridor surface preserved from current Desktop. Status strip and decision continuity now share tokens with this pane — internal flow unchanged." />}
            {surface === "paper"       && <StubSurface       title="Paper Operations" note="Paper sessions, alerts, and supervised promotion controls. Now reachable from the System surface session table without a tab swap." />}
            {surface === "experiments" && <StubSurface       title="Experiments" note="Sweep configs (configs/experiments) and recent sweep outputs (outputs/sweeps). Sweep decision handoff preserved; visuals harmonised with the new token set." />}
            {surface === "launch"      && <StubSurface       title="Launch" note="Primary launch workspace. Form layout converges to the same panel/eyebrow vocabulary as Runs and Compare." />}
            {surface === "candidates"  && <StubSurface       title="Candidates" note="Shortlist + baseline editor. Shares spotlight + decision-queue components with Runs to remove cross-surface fragmentation." />}
            {surface === "assistant"   && <StubSurface       title="Assistant" note="Deterministic QuantLab command lane. Stepbit-backed adapter routed via explicit `ask stepbit …`. Visual chrome converges with main shell." />}
          </div>
        </div>
      </div>

      <TweaksPanel title="Tweaks">
        <TweakSection label="Density">
          <TweakRadio label="Rows" value={t.density} options={["compact", "default", "comfortable"]} onChange={(v) => setT("density", v)} />
        </TweakSection>
        <TweakSection label="Accent">
          <TweakColor label="Hue" value={t.accent}
            options={["#62d4ff", "#7fa6ff", "#9ec5d9", "#a8e2c2"]}
            onChange={(v) => setT("accent", v)} />
        </TweakSection>
        <TweakSection label="Table">
          <TweakRadio label="Gridlines" value={t.gridlines} options={["on","off"]} onChange={(v) => setT("gridlines", v)} />
        </TweakSection>
        <TweakSection label="Type">
          <TweakSelect label="Mono font" value={t.monoFont} options={["JetBrains Mono", "IBM Plex Mono", "ui-monospace"]} onChange={(v) => setT("monoFont", v)} />
        </TweakSection>
      </TweaksPanel>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
