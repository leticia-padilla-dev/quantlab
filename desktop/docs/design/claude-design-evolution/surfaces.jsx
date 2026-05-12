// QuantLab Desktop — Surface panes (Runs, Run Detail, Compare, System, Paper Ops, generic)

const { useState: useS, useMemo: useM } = React;

// ─── Runs surface ────────────────────────────────────────
function RunsSurface({ onOpenRun, onCompare }) {
  const [selected, setSelected] = useS(["wf_2026-05-09_btc-mr_03", "wf_2026-05-08_btc-mr_02"]);
  const [filter, setFilter] = useS("all");
  const [query, setQuery] = useS("");

  const runs = useM(() => RUNS.filter((r) => {
    if (filter === "candidates" && !r.candidate) return false;
    if (filter === "walkforward" && r.mode !== "walkforward") return false;
    if (filter === "pass" && r.verdict !== "pass") return false;
    if (query && !r.id.includes(query) && !r.strategy.includes(query)) return false;
    return true;
  }), [filter, query]);

  const baseline = RUNS.find((r) => r.baseline);
  const spotlight = RUNS.find((r) => r.id === selected[0]) || baseline || RUNS[0];
  const candidates = RUNS.filter((r) => r.candidate).length;
  const shortlisted = RUNS.filter((r) => r.shortlisted).length;
  const compareReady = selected.length >= 2 || shortlisted >= 2;

  const toggleSel = (id) => setSelected((s) =>
    s.includes(id) ? s.filter((x) => x !== id) : s.length >= 4 ? s : [...s, id]
  );

  return (
    <>
      <div className="kpi-strip">
        <div className="kpi"><div className="eyebrow">Indexed</div><div className="kpi-value">{RUNS.length}</div><div className="kpi-sub">runs · last 7d</div></div>
        <div className="kpi"><div className="eyebrow">Candidates</div><div className="kpi-value tone-info">{candidates}</div><div className="kpi-sub">marked for review</div></div>
        <div className="kpi"><div className="eyebrow">Shortlisted</div><div className="kpi-value tone-positive">{shortlisted}</div><div className="kpi-sub">decision queue</div></div>
        <div className="kpi"><div className="eyebrow">Baseline</div><div className="kpi-value mono" style={{ fontSize: 13 }}>{baseline ? shortId(baseline.id) : "—"}</div><div className="kpi-sub">promotion anchor</div></div>
        <div className="kpi"><div className="eyebrow">Paper</div><div className="kpi-value tone-positive">Ready</div><div className="kpi-sub">3 sessions live</div></div>
      </div>

      <div className="runs-layout">
        <div className="runs-table-wrap">
          <div className="runs-toolbar">
            <Icon d={ICONS.search} />
            <input className="search" placeholder="filter run id, strategy…" value={query} onChange={(e) => setQuery(e.target.value)} />
            {["all", "candidates", "walkforward", "pass"].map((f) => (
              <button key={f} className={`filter-chip ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>{f}</button>
            ))}
          </div>
          <table className="runs-table">
            <thead>
              <tr>
                <th style={{ width: 28 }}></th>
                <th>Run · Strategy</th>
                <th style={{ width: 60 }}>Mode</th>
                <th>Metrics</th>
                <th>Status</th>
                <th style={{ width: 90 }}>Started</th>
                <th style={{ width: 150, textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 && (
                <tr><td colSpan="7" className="empty-table">No runs match this filter.</td></tr>
              )}
              {runs.map((r) => (
                <tr key={r.id} className={selected.includes(r.id) ? "selected" : ""}>
                  <td><input type="checkbox" checked={selected.includes(r.id)} onChange={() => toggleSel(r.id)} /></td>
                  <td><div className="run-id">{r.id}<span className="strat">{r.strategy} · {r.universe}</span></div></td>
                  <td><span className={`mode-glyph ${r.mode === "walkforward" ? "wf" : "bt"}`}>{r.mode === "walkforward" ? "WF" : "BT"}</span></td>
                  <td>
                    <div className="metric-cell">
                      <span className="metric-chip"><span className="lbl">ret</span><span className={tone(r.total_return)}>{fmtPct(r.total_return)}</span></span>
                      <span className="metric-chip"><span className="lbl">shp</span><span>{fmtNum(r.sharpe)}</span></span>
                      <span className="metric-chip"><span className="lbl">dd</span><span className={tone(r.max_drawdown, false)}>{fmtPct(r.max_drawdown)}</span></span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                      <span className={`badge ${r.verdict}`}>{r.verdict}</span>
                      {r.baseline && <span className="badge baseline">baseline</span>}
                      {r.shortlisted && !r.baseline && <span className="badge shortlist">shortlist</span>}
                    </div>
                  </td>
                  <td><span className="mono" style={{ fontSize: 10.5, color: "var(--muted)" }}>{r.started.split(" ")[1]}<br/><span style={{ color: "var(--muted-dark)" }}>{r.started.split(" ")[0].slice(5)}</span></span></td>
                  <td>
                    <div className="row-actions">
                      <button className="btn mini" onClick={() => onOpenRun(r.id)}>Open</button>
                      <button className="btn mini">Explore</button>
                      <button className="btn mini" title="Mark candidate">★</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="runs-rail">
          <div className="rail-card">
            <span className="eyebrow">Spotlight</span>
            <h4>{selected.length ? "Selected run" : baseline ? "Baseline" : "Latest run"}</h4>
            <div className="spotlight-id">{spotlight?.id}</div>
            <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>
              {spotlight?.baseline && <span className="badge baseline">baseline</span>}
              <span className={`badge ${spotlight?.verdict || "review"}`}>{spotlight?.verdict}</span>
            </div>
            <dl className="spotlight-metrics">
              <div><dt>Return</dt><dd className={tone(spotlight?.total_return)}>{fmtPct(spotlight?.total_return)}</dd></div>
              <div><dt>Sharpe</dt><dd>{fmtNum(spotlight?.sharpe)}</dd></div>
              <div><dt>Drawdown</dt><dd className={tone(spotlight?.max_drawdown, false)}>{fmtPct(spotlight?.max_drawdown)}</dd></div>
              <div><dt>Trades</dt><dd>{spotlight?.trades}</dd></div>
            </dl>
            <div style={{ marginTop: 12, display: "flex", gap: 6 }}>
              <button className="btn mini" style={{ flex: 1 }} onClick={() => spotlight && onOpenRun(spotlight.id)}>Open detail →</button>
            </div>
          </div>

          <div className="rail-card">
            <span className="eyebrow">Decision queue</span>
            <h4>Promotion state</h4>
            <div className="decision-queue" style={{ marginTop: 8 }}>
              <div className="dq-cell"><div className="eyebrow">Marked</div><span className="num tone-info">{candidates}</span></div>
              <div className="dq-cell"><div className="eyebrow">Short</div><span className="num tone-positive">{shortlisted}</span></div>
              <div className="dq-cell"><div className="eyebrow">Selected</div><span className="num">{selected.length}</span></div>
            </div>
            <button className="btn primary" style={{ width: "100%", justifyContent: "center" }} disabled={!compareReady} onClick={() => onCompare(selected)}>
              <Icon d={ICONS.compare} /> Compare {selected.length >= 2 ? `${selected.length} selected` : `shortlist`}
            </button>
            <div className="rail-divider"></div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Continuity</div>
            <div style={{ fontSize: 11.5, color: "var(--muted)", lineHeight: 1.5 }}>
              Selection persisted to <span className="mono" style={{ color: "var(--text-soft)" }}>outputs/desktop/<wbr/>candidates_shortlist.json</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Run Detail surface ──────────────────────────────────
function RunDetailSurface({ runId, onBack, onCompare }) {
  const run = RUNS.find((r) => r.id === runId) || RUNS[0];
  const lineageSteps = [
    { state: "done", title: "Config resolved",       meta: "configs/strategies/mean-reversion-v3.yaml" },
    { state: "done", title: "Run launched",          meta: `${run.commit} · ${run.started}` },
    { state: "done", title: "Artifacts emitted",     meta: `${run.artifacts} files · 1.07 MB` },
    { state: run.verdict === "pass" ? "done" : run.verdict === "review" ? "warn" : "warn",
      title: "Robustness verdict", meta: `${run.verdict.toUpperCase()} · walkforward folds` },
    { state: "current", title: "Decision",            meta: run.baseline ? "Baseline · promoted" : run.shortlisted ? "Shortlisted · pending" : "Awaiting review" },
    { state: run.baseline ? "current" : "",           title: "Promotion to Paper", meta: run.baseline ? "ps_btc-mr_2026-05-09 · live" : "Not promoted" },
  ];

  return (
    <div className="run-detail-layout">
      <div className="lineage">
        <h4>Evidence lineage</h4>
        {lineageSteps.map((s, i) => (
          <div key={i} className={`lineage-step ${s.state}`}>
            <div className="node"></div>
            <div>
              <div className="step-title">{s.title}</div>
              <div className="step-meta">{s.meta}</div>
            </div>
          </div>
        ))}
      </div>

      <div>
        <div className="run-header">
          <div className="run-header-top">
            <div style={{ minWidth: 0, flex: 1 }}>
              <div className="eyebrow">Run</div>
              <h2>{run.id}</h2>
              <div className="run-meta-row">
                <span>strategy<strong>{run.strategy}</strong></span>
                <span>universe<strong>{run.universe}</strong></span>
                <span>commit<strong className="mono">{run.commit}</strong></span>
                <span>duration<strong>{run.duration}</strong></span>
                <span>started<strong>{run.started}</strong></span>
              </div>
            </div>
            <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
              <button className="btn mini" onClick={onBack}>← Runs</button>
              <button className="btn mini">Open folder</button>
            </div>
          </div>
          <div className="run-metric-grid">
            <div className="run-metric"><div className="eyebrow">Total return</div><div className={`v ${tone(run.total_return)}`}>{fmtPct(run.total_return)}</div></div>
            <div className="run-metric"><div className="eyebrow">Sharpe (simple)</div><div className="v">{fmtNum(run.sharpe)}</div></div>
            <div className="run-metric"><div className="eyebrow">Max drawdown</div><div className={`v ${tone(run.max_drawdown, false)}`}>{fmtPct(run.max_drawdown)}</div></div>
            <div className="run-metric"><div className="eyebrow">Trades</div><div className="v">{run.trades}</div></div>
          </div>
        </div>

        <div className={`verdict-block ${run.verdict}`}>
          <div className="verdict-headline">
            <span className={`badge ${run.verdict}`}>{run.verdict}</span>
            <h3 className={tone(run.verdict === "pass" ? 1 : run.verdict === "review" ? 0 : -1, false)}>
              {run.verdict === "pass" ? "Robustness verdict: PASS" : run.verdict === "review" ? "Robustness verdict: REVIEW" : "Robustness verdict: FAIL"}
            </h3>
          </div>
          <p className="verdict-recommendation">
            {run.verdict === "pass"
              ? "Walkforward folds are consistent within tolerance. Stress envelopes within budget. Run is eligible for shortlist promotion and supervised paper handoff."
              : run.verdict === "review"
              ? "Walkforward dispersion above warn threshold on 2/5 folds. Inspect fold returns and slippage assumptions before promotion."
              : "One or more guards failed: drawdown breach on out-of-sample folds. Promotion blocked until reconfigured."}
          </p>
          <ul className="verdict-reasons">
            <li>walkforward.fold_consistency = 0.83 (threshold 0.80)</li>
            <li>stress.shock_2σ.drawdown = -0.094 (within budget -0.15)</li>
            <li>execution.slippage_realised = 2.7 bps (cfg 3 bps)</li>
          </ul>
        </div>

        <div className="panel" style={{ marginBottom: 16 }}>
          <div className="panel-head">
            <div>
              <span className="eyebrow">Artifacts · {run.artifacts} files</span>
              <h3>Evidence package</h3>
            </div>
            <button className="btn mini"><Icon d={ICONS.download} /> Download all</button>
          </div>
          <div className="panel-body" style={{ padding: 0 }}>
            <div className="artifact-list">
              {ARTIFACTS.map((a) => (
                <div key={a.name} className="artifact-row">
                  <span className={`artifact-icon ${a.kind}`}>{a.kind.charAt(0).toUpperCase()}</span>
                  <span className="artifact-name">{a.name}{!a.required && <small>optional</small>}</span>
                  <span className="artifact-size">{a.size}</span>
                  <button className="btn mini">Open</button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="decision-dock">
        <div className="rail-card">
          <span className="eyebrow">Decision</span>
          <h4>Promotion controls</h4>
          <div style={{ display: "grid", gap: 6, marginTop: 10 }}>
            <button className="btn primary" style={{ justifyContent: "center" }}>
              {run.baseline ? "✓ Baseline" : "Set as baseline"}
            </button>
            <button className="btn" style={{ justifyContent: "center" }}>
              {run.shortlisted ? "✓ Shortlisted" : "Shortlist"}
            </button>
            <button className="btn" style={{ justifyContent: "center" }} onClick={() => onCompare([run.id])}>
              Compare against baseline
            </button>
          </div>
          <div className="rail-divider"></div>
          <span className="eyebrow">Promote to paper</span>
          <p style={{ fontSize: 11.5, color: "var(--muted)", margin: "6px 0 8px", lineHeight: 1.5 }}>
            Desktop is review-only. Paper handoff requires explicit operator action.
          </p>
          <button className="btn" style={{ width: "100%", justifyContent: "center" }} disabled={run.verdict !== "pass"}>
            Open paper handoff →
          </button>
        </div>

        <div className="rail-card">
          <span className="eyebrow">Related runs</span>
          <h4>Same strategy</h4>
          <div style={{ display: "grid", gap: 6, marginTop: 8 }}>
            {RUNS.filter((r) => r.strategy === run.strategy && r.id !== run.id).slice(0, 3).map((r) => (
              <div key={r.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11, padding: "6px 8px", background: "var(--ink-750)", borderRadius: 4 }}>
                <span className="mono" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{shortId(r.id)}</span>
                <span className={`badge ${r.verdict}`}>{r.verdict}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Compare surface ─────────────────────────────────────
function CompareSurface({ runIds, onOpenRun }) {
  const ids = runIds && runIds.length >= 2 ? runIds : RUNS.filter((r) => r.shortlisted || r.baseline).map((r) => r.id);
  const runs = ids.map((id) => RUNS.find((r) => r.id === id)).filter(Boolean);
  const [metric, setMetric] = useS("sharpe");
  const ranked = [...runs].sort((a, b) => metric === "max_drawdown" ? a[metric] - b[metric] : b[metric] - a[metric]);
  const winner = ranked[0];

  return (
    <>
      <div className="kpi-strip">
        <div className="kpi"><div className="eyebrow">Compared</div><div className="kpi-value">{runs.length}</div><div className="kpi-sub">runs in set</div></div>
        <div className="kpi"><div className="eyebrow">Rank by</div><div className="kpi-value" style={{ fontSize: 14 }}>{metric}</div><div className="kpi-sub">higher = better</div></div>
        <div className="kpi"><div className="eyebrow">Winner</div><div className="kpi-value mono tone-positive" style={{ fontSize: 13 }}>{winner ? shortId(winner.id) : "—"}</div><div className="kpi-sub">{winner ? fmtNum(winner[metric]) : ""}</div></div>
        <div className="kpi"><div className="eyebrow">Baseline in set</div><div className="kpi-value" style={{ fontSize: 13 }}>{runs.find((r) => r.baseline) ? "yes" : "no"}</div><div className="kpi-sub">{runs.find((r) => r.baseline) ? shortId(runs.find((r) => r.baseline).id) : "—"}</div></div>
        <div className="kpi"><div className="eyebrow">Shortlisted</div><div className="kpi-value tone-positive">{runs.filter((r) => r.shortlisted).length}</div><div className="kpi-sub">of {runs.length}</div></div>
      </div>

      <div className="runs-layout">
        <div style={{ display: "grid", gap: 16 }}>
          <div className="panel">
            <div className="panel-head">
              <div>
                <span className="eyebrow">Ranking matrix</span>
                <h3>Decision-ready compare</h3>
              </div>
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <span className="eyebrow">rank by</span>
                <select className="btn mini" value={metric} onChange={(e) => setMetric(e.target.value)} style={{ background: "var(--ink-850)" }}>
                  <option value="sharpe">Sharpe</option>
                  <option value="total_return">Return</option>
                  <option value="max_drawdown">Drawdown</option>
                  <option value="trades">Trades</option>
                </select>
              </div>
            </div>
            <table className="compare-table">
              <thead>
                <tr><th style={{width:30}}>#</th><th>Run</th><th>Mode</th><th>{metric}</th><th>Return</th><th>Sharpe</th><th>Drawdown</th><th>Trades</th><th>Verdict</th></tr>
              </thead>
              <tbody>
                {ranked.map((r, i) => (
                  <tr key={r.id} className={i === 0 ? "winner" : ""}>
                    <td><span className={`rank-num ${i === 0 ? "first" : ""}`}>{i + 1}</span></td>
                    <td><a href="#" onClick={(e) => { e.preventDefault(); onOpenRun(r.id); }} style={{ color: "var(--text)", textDecoration: "none" }}>{r.id}</a></td>
                    <td>{r.mode === "walkforward" ? "WF" : "BT"}</td>
                    <td className={i === 0 ? "tone-positive" : ""}>{fmtNum(r[metric])}</td>
                    <td className={tone(r.total_return)}>{fmtPct(r.total_return)}</td>
                    <td>{fmtNum(r.sharpe)}</td>
                    <td className={tone(r.max_drawdown, false)}>{fmtPct(r.max_drawdown)}</td>
                    <td>{r.trades}</td>
                    <td><span className={`badge ${r.verdict}`}>{r.verdict}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="panel">
            <div className="panel-head">
              <div>
                <span className="eyebrow">Config deltas · {CONFIG_DELTAS.length} keys</span>
                <h3>What changed across this set</h3>
              </div>
            </div>
            <table className="delta-table">
              <thead><tr><th>Key</th>{ranked.map((r) => <th key={r.id}>{shortId(r.id)}</th>)}</tr></thead>
              <tbody>
                {CONFIG_DELTAS.map(([key, vals]) => (
                  <tr key={key}>
                    <td style={{ color: "var(--muted)" }}>{key}</td>
                    {vals.slice(0, ranked.length).map((v, i) => (
                      <td key={i}><span className={`delta-val ${i === 0 ? "winner" : ""}`}>{v}</span></td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="runs-rail">
          <div className="rail-card">
            <span className="eyebrow">Current leader</span>
            <h4>{winner?.id}</h4>
            <div className="spotlight-id" style={{ marginBottom: 6, color: "var(--muted)", fontSize: 10.5 }}>{winner?.strategy} · {winner?.universe}</div>
            <dl className="spotlight-metrics">
              <div><dt>{metric}</dt><dd className="tone-positive">{fmtNum(winner?.[metric])}</dd></div>
              <div><dt>Return</dt><dd className={tone(winner?.total_return)}>{fmtPct(winner?.total_return)}</dd></div>
              <div><dt>Sharpe</dt><dd>{fmtNum(winner?.sharpe)}</dd></div>
              <div><dt>Drawdown</dt><dd className={tone(winner?.max_drawdown, false)}>{fmtPct(winner?.max_drawdown)}</dd></div>
            </dl>
            <button className="btn primary" style={{ width: "100%", justifyContent: "center", marginTop: 12 }} onClick={() => onOpenRun(winner?.id)}>Open detail →</button>
          </div>
          <div className="rail-card">
            <span className="eyebrow">Promote</span>
            <h4>Decision actions</h4>
            <div style={{ display: "grid", gap: 6, marginTop: 8 }}>
              <button className="btn">Set winner as baseline</button>
              <button className="btn">Shortlist winner</button>
              <button className="btn" disabled>Promote to paper</button>
            </div>
            <p style={{ fontSize: 11, color: "var(--muted)", margin: "10px 0 0", lineHeight: 1.5 }}>
              Promotion to paper requires <span className="mono" style={{ color: "var(--text-soft)" }}>verdict=pass</span> on the winning run.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── System surface ──────────────────────────────────────
function SystemSurface() {
  const ticks = Array.from({ length: 40 }, (_, i) => i);
  return (
    <>
      <div className="kpi-strip">
        <div className="kpi"><div className="eyebrow">Runtime</div><div className="kpi-value tone-positive">Ready</div><div className="kpi-sub">research_ui · uptime 4h 12m</div></div>
        <div className="kpi"><div className="eyebrow">Corridor</div><div className="kpi-value tone-positive">OK</div><div className="kpi-sub">3 sessions · last 12s</div></div>
        <div className="kpi"><div className="eyebrow">Reachability</div><div className="kpi-value tone-positive">100%</div><div className="kpi-sub">120/120 last hour</div></div>
        <div className="kpi"><div className="eyebrow">Alerts (24h)</div><div className="kpi-value tone-warning">1</div><div className="kpi-sub">eth-mom · order delay</div></div>
        <div className="kpi"><div className="eyebrow">Local storage</div><div className="kpi-value">68%</div><div className="kpi-sub">14.2 GB · outputs/</div></div>
      </div>

      <div className="system-grid">
        <div style={{ display: "grid", gap: 16 }}>
          <div className="health-card">
            <h3>Corridor health · last 40 ticks</h3>
            <div className="health-meter">
              {ticks.map((i) => (
                <div key={i} className={`health-tick ${i === 22 ? "warn" : i > 38 ? "idle" : ""}`}></div>
              ))}
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10.5, color: "var(--muted-dark)", fontFamily: "var(--font-mono)" }}>
              <span>−40m</span><span>−20m</span><span>now</span>
            </div>
          </div>

          <div className="health-card">
            <h3>Paper sessions</h3>
            <div className="session-list">
              {PAPER_SESSIONS.map((s) => (
                <div key={s.id} className="session-row">
                  <div className="sid">{s.id}<small>{s.strategy} · {s.universe}</small></div>
                  <span className={s.state === "running" ? "tone-positive" : "tone-warning"}>{s.state}</span>
                  <span className={tone(s.pnl)}>{fmtPct(s.pnl)}</span>
                  <span>{s.orders}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gap: 16 }}>
          <div className="health-card">
            <h3>Corridor signals</h3>
            <div className="corridor-rows">
              <div className="corridor-row"><span className="lbl">Root alert</span><span className="val tone-positive">{CORRIDOR.root_alert.toUpperCase()}</span></div>
              <div className="corridor-row"><span className="lbl">Sessions</span><span className="val">{CORRIDOR.sessions}</span></div>
              <div className="corridor-row"><span className="lbl">Latest order</span><span className="val tone-positive">{CORRIDOR.latest_order}</span></div>
              <div className="corridor-row"><span className="lbl">Latest submit</span><span className="val tone-positive">{CORRIDOR.latest_submit}</span></div>
              <div className="corridor-row"><span className="lbl">Reachability</span><span className="val tone-positive">{CORRIDOR.reachability}</span></div>
              <div className="corridor-row"><span className="lbl">Last check</span><span className="val">{CORRIDOR.last_check}</span></div>
            </div>
          </div>
          <div className="health-card">
            <h3>Operator notice</h3>
            <p style={{ fontSize: 12.5, color: "var(--text-soft)", margin: 0, lineHeight: 1.55 }}>
              Desktop is an <strong>operator workspace and review surface</strong>. It is not a second execution authority. Paper handoff is supervised and requires explicit confirmation.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Stub for less-detailed surfaces ─────────────────────
function StubSurface({ title, note }) {
  return (
    <div className="panel" style={{ maxWidth: 640 }}>
      <div className="panel-head"><div><span className="eyebrow">Surface</span><h3>{title}</h3></div></div>
      <div className="panel-body">
        <p style={{ margin: 0, color: "var(--muted)", fontSize: 12.5, lineHeight: 1.55 }}>
          {note || "Surface preserved from current shell. Evolution focuses on cross-cutting layout, status strip, and decision continuity — surface internals remain identical to current Desktop pane."}
        </p>
      </div>
    </div>
  );
}

Object.assign(window, { RunsSurface, RunDetailSurface, CompareSurface, SystemSurface, StubSurface });
