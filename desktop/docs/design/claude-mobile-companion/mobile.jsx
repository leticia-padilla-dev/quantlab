// QuantLab Mobile Companion — read-only operator app
// All 8 screens. Each lives inside an iOS-style frame.
// Tab nav is interactive within a single artboard; other artboards are static states.

const { useState } = React;

// ─── icons ────────────────────────────────────────────────────────────
const IC = {
  home: <path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z" />,
  runs: <g><path d="M4 6h16M4 12h16M4 18h10" /><circle cx="18" cy="18" r="2" /></g>,
  alert: <g><path d="M12 3l10 17H2z" /><path d="M12 10v5M12 17v.5" /></g>,
  gate: <g><rect x="3" y="10" width="18" height="11" rx="2" /><path d="M7 10V7a5 5 0 0 1 10 0v3" /></g>,
  more: <g><circle cx="5" cy="12" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="19" cy="12" r="1.5" /></g>,
  artifact: <g><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6" /></g>,
  bell: <g><path d="M6 8a6 6 0 1 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9z" /><path d="M10 21a2 2 0 0 0 4 0" /></g>,
  asst: <g><circle cx="12" cy="12" r="9" /><path d="M8 10c1-2 3-2 4 0M16 10c-1-2-3-2-4 0M9 16c1 1 5 1 6 0" /></g>,
  settings: <g><circle cx="12" cy="12" r="3" /><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.4.9a7 7 0 0 0-2-1.2L14 3h-4l-.5 2.5a7 7 0 0 0-2 1.2L5 5.8 3 9.2l2 1.6A7 7 0 0 0 5 12c0 .4 0 .8.1 1.2l-2 1.6 2 3.4 2.4-.9c.6.5 1.3.9 2 1.2L10 21h4l.5-2.5c.7-.3 1.4-.7 2-1.2l2.4.9 2-3.4-2-1.6c.1-.4.1-.8.1-1.2z" /></g>,
  lock: <g><rect x="5" y="11" width="14" height="9" rx="1.5" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></g>,
  eye: <g><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></g>,
  chev: <path d="M9 6l6 6-6 6" />,
  check: <path d="M5 12l5 5L20 6" />,
  x: <path d="M6 6l12 12M18 6L6 18" />,
  pause: <g><rect x="6" y="5" width="4" height="14" /><rect x="14" y="5" width="4" height="14" /></g>,
};

const Icon = ({ k, size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">{IC[k]}</svg>
);

// ─── chrome ───────────────────────────────────────────────────────────
function StatusBar() {
  return (
    <div style={{
      height: 44, padding: '0 22px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      fontFamily: 'var(--font-ui)', fontSize: 14, fontWeight: 600, color: 'var(--text)',
      fontVariantNumeric: 'tabular-nums',
    }}>
      <span style={{ fontFamily: 'var(--font-mono)' }}>09:41</span>
      <span style={{ display: 'flex', gap: 6, alignItems: 'center', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)' }}>
        QL · LAN
      </span>
      <span style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
        <svg width="16" height="11" viewBox="0 0 16 11" fill="currentColor"><rect x="0" y="7" width="3" height="4" rx="0.5"/><rect x="4" y="5" width="3" height="6" rx="0.5"/><rect x="8" y="3" width="3" height="8" rx="0.5"/><rect x="12" y="0" width="3" height="11" rx="0.5"/></svg>
        <svg width="22" height="11" viewBox="0 0 22 11" fill="none" stroke="currentColor" strokeWidth="1"><rect x="0.5" y="0.5" width="18" height="10" rx="2"/><rect x="2" y="2" width="13" height="7" rx="1" fill="currentColor"/><rect x="19" y="3.5" width="1.5" height="4" rx="0.5" fill="currentColor"/></svg>
      </span>
    </div>
  );
}

function Header({ eyebrow, title, readonly = true }) {
  return (
    <div className="m-header">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <div className="title">{title}</div>
      </div>
      {readonly && (
        <span className="pill"><span className="dot" />Read · Only</span>
      )}
    </div>
  );
}

function Strip({ cells }) {
  return (
    <div className="m-strip">
      {cells.map((c, i) => (
        <div key={i} className="cell">
          <div className="k">{c.k}</div>
          <div className={`v ${c.tone || ''}`}>{c.v}</div>
        </div>
      ))}
    </div>
  );
}

function ReadOnly({ msg = 'Companion · Review surface · No execution authority' }) {
  return (
    <div className="m-readonly">
      <svg className="ic" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="9" rx="1.5" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg>
      {msg}
    </div>
  );
}

function TabBar({ active, onPick }) {
  const items = [
    { k: 'home', label: 'Home' },
    { k: 'runs', label: 'Runs' },
    { k: 'alert', label: 'Alerts' },
    { k: 'gate', label: 'Gate' },
    { k: 'more', label: 'More' },
  ];
  return (
    <div className="m-tabbar">
      {items.map(it => (
        <button key={it.k} className={`m-tab ${active === it.k ? 'active' : ''}`} onClick={() => onPick && onPick(it.k)}>
          <Icon k={it.k} />
          <span>{it.label}</span>
        </button>
      ))}
    </div>
  );
}

// ─── tiny visualizations ─────────────────────────────────────────────
function Sparkline({ pts, tone = 'accent' }) {
  const stroke = tone === 'success' ? 'var(--success)' : tone === 'warn' ? 'var(--warn)' : 'var(--accent)';
  const w = 200, h = 36;
  const min = Math.min(...pts), max = Math.max(...pts);
  const span = max - min || 1;
  const path = pts.map((p, i) => {
    const x = (i / (pts.length - 1)) * w;
    const y = h - ((p - min) / span) * (h - 4) - 2;
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  return (
    <svg className="m-spark" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <path d={path} fill="none" stroke={stroke} strokeWidth="1.2" />
      <path d={`${path} L${w},${h} L0,${h} Z`} fill={stroke} opacity="0.10" />
    </svg>
  );
}

function HealthMeter({ ticks }) {
  return (
    <div className="m-meter">
      {ticks.map((t, i) => <span key={i} className={t.cls} style={{ height: `${t.h}%` }} />)}
    </div>
  );
}

// ─── data (mirrors desktop) ───────────────────────────────────────────
const MOBILE_DATA = {
  runs: [
    { id: 'r-7a3f', name: 'momentum-15m · v0.42', verdict: 'pass', sharpe: '1.82', dd: '4.1%', oos: '+0.14' },
    { id: 'r-7a3e', name: 'mean-rev-1h · v0.31', verdict: 'cand', sharpe: '1.41', dd: '6.8%', oos: '+0.06' },
    { id: 'r-7a3d', name: 'breakout-5m · v0.18', verdict: 'fail', sharpe: '0.62', dd: '11.4%', oos: '−0.08' },
    { id: 'r-7a3c', name: 'pairs-eth-btc · v0.09', verdict: 'pass', sharpe: '1.66', dd: '3.7%', oos: '+0.11' },
    { id: 'r-7a3b', name: 'vol-carry · v0.22', verdict: 'cand', sharpe: '1.28', dd: '7.2%', oos: '+0.04' },
  ],
  alerts: [
    { lvl: 'warn', h: 'Corridor drift · liquidity z=2.1', s: 'maker-5m · BTC · 12 min ago', t: '12m' },
    { lvl: 'info', h: 'Run r-7a3f promoted to D.2', s: 'evidence pack · auto-attached', t: '1h' },
    { lvl: 'danger', h: 'Reachability degraded · 1/3 nodes', s: 'index-node-02 · timeout', t: '2h' },
    { lvl: 'info', h: 'Paper session paused', s: 'session ps-44a · operator action', t: '4h' },
    { lvl: 'warn', h: 'Walk-forward variance widened', s: 'momentum-15m · σ +18%', t: '6h' },
  ],
};

// ═════════════════════════════════════════════════════════════════════
// SCREEN 1 — Home / Overview
// ═════════════════════════════════════════════════════════════════════
function HomeScreen({ tab = 'home', setTab }) {
  const ticks = Array.from({ length: 30 }, (_, i) => ({
    h: 30 + (Math.sin(i * 0.4) * 18 + 22) + (i % 7 === 0 ? 22 : 0),
    cls: i === 27 ? 'warn' : i === 29 ? 'warn' : 'ok',
  }));
  return (
    <div className="m-screen">
      <StatusBar />
      <Header eyebrow="Operator · Overview" title="Good morning" />
      <Strip cells={[
        { k: 'Runtime', v: 'Live', tone: 'ok' },
        { k: 'Corridor', v: 'Hold', tone: 'warn' },
        { k: 'Reach', v: '2 / 3', tone: 'warn' },
      ]} />
      <div className="m-body">
        <div className="m-card elev">
          <div className="m-sec" style={{ margin: 0 }}>
            <span className="label">Today · D.2 / D.3 promotion</span>
            <span className="count">11:00 UTC</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10 }}>
            <div className="m-bigmetric">
              <span className="v">3<span style={{ color: 'var(--muted)', fontSize: 16 }}> / 7</span></span>
              <span className="d">Candidates passing gate</span>
            </div>
            <div className="m-bigmetric">
              <span className="v" style={{ color: 'var(--accent)' }}>2</span>
              <span className="d">Awaiting operator review</span>
            </div>
          </div>
        </div>

        <div className="m-sec"><span className="label">System Health · 30m</span><span className="count">98.6% uptime</span></div>
        <div className="m-card">
          <HealthMeter ticks={ticks} />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)' }}>
            <span>−30m</span><span>−15m</span><span>now</span>
          </div>
        </div>

        <div className="m-sec"><span className="label">Recent activity</span><span className="count">last 6h</span></div>
        <div className="m-card" style={{ padding: 0 }}>
          <div className="m-timeline" style={{ padding: 14 }}>
            <div className="step done"><div className="dot" /><div className="body"><div className="h">r-7a3f promoted to D.2</div><div className="s">01:14 · evidence pack attached</div></div></div>
            <div className="step warn"><div className="dot" /><div className="body"><div className="h">Corridor drift detected</div><div className="s">00:48 · liquidity z=2.1 · maker-5m</div></div></div>
            <div className="step done"><div className="dot" /><div className="body"><div className="h">Paper session ps-44a paused</div><div className="s">23:02 · operator action</div></div></div>
            <div className="step active"><div className="dot" /><div className="body"><div className="h">Reachability degraded</div><div className="s">22:11 · index-node-02 timeout</div></div></div>
          </div>
        </div>
      </div>
      <TabBar active={tab} onPick={setTab} />
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// SCREEN 2 — Runs list
// ═════════════════════════════════════════════════════════════════════
function RunsScreen({ tab = 'runs', setTab }) {
  const [filter, setFilter] = useState('all');
  const runs = MOBILE_DATA.runs.filter(r => filter === 'all' || r.verdict === filter);
  return (
    <div className="m-screen">
      <StatusBar />
      <Header eyebrow="Operations" title="Runs" />
      <Strip cells={[
        { k: 'Today', v: '24', tone: '' },
        { k: 'Pass', v: '11', tone: 'ok' },
        { k: 'Cand', v: '7', tone: '' },
      ]} />
      <div style={{ padding: '14px 16px 8px' }}>
        <div className="m-chips">
          {[['all','All'],['pass','Pass'],['cand','Cand'],['fail','Fail']].map(([k,l]) => (
            <button key={k} className={`m-chip ${filter === k ? 'active' : ''}`} onClick={() => setFilter(k)}>{l}</button>
          ))}
        </div>
      </div>
      <div className="m-body" style={{ paddingTop: 4 }}>
        {runs.map(r => (
          <div key={r.id} className="m-run">
            <div className="top">
              <div>
                <div className="id">{r.id}</div>
                <div className="name">{r.name}</div>
              </div>
              <span className={`m-badge ${r.verdict}`}>{r.verdict === 'cand' ? 'candidate' : r.verdict}</span>
            </div>
            <div className="metrics">
              <div className="col"><span className="k">Sharpe</span><span className="v">{r.sharpe}</span></div>
              <div className="col"><span className="k">Max DD</span><span className="v">{r.dd}</span></div>
              <div className="col"><span className="k">OOS Δ</span><span className="v" style={{ color: r.oos.startsWith('+') ? 'var(--success)' : 'var(--danger)' }}>{r.oos}</span></div>
            </div>
          </div>
        ))}
      </div>
      <TabBar active={tab} onPick={setTab} />
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// SCREEN 3 — Run Detail / evidence
// ═════════════════════════════════════════════════════════════════════
function RunDetailScreen({ tab = 'runs', setTab }) {
  const equity = [100, 102, 101.4, 104, 106, 105.2, 107, 109, 108, 111, 113, 112.4, 115, 117, 116, 119, 121];
  return (
    <div className="m-screen">
      <StatusBar />
      <div style={{ padding: '12px 16px 10px', borderBottom: '1px solid var(--line-soft)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <button style={{ color: 'var(--muted)' }}><Icon k="chev" size={20} color="var(--muted)" /></button>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.10em', color: 'var(--muted)' }}>r-7a3f · v0.42</div>
          <div style={{ fontSize: 17, fontWeight: 600, marginTop: 2 }}>momentum-15m</div>
        </div>
        <span className="m-badge pass">pass</span>
      </div>
      <div className="m-body">
        <div className="m-card elev">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <div className="m-bigmetric"><span className="v" style={{ color: 'var(--success)' }}>+18.4%</span><span className="d">OOS equity · 90d walk-forward</span></div>
            <span className="m-badge pass">verdict</span>
          </div>
          <div style={{ marginTop: 10 }}><Sparkline pts={equity} tone="success" /></div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--line-soft)' }}>
            {[['Sharpe','1.82'],['Sortino','2.41'],['Max DD','4.1%'],['Win %','58.3']].map(([k,v]) => (
              <div key={k} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <span className="k" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)', letterSpacing: '0.10em', textTransform: 'uppercase' }}>{k}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="m-sec"><span className="label">Evidence Timeline</span><span className="count">7 steps</span></div>
        <div className="m-card" style={{ padding: 14 }}>
          <div className="m-timeline">
            <div className="step done"><div className="dot" /><div className="body"><div className="h">Config locked · cfg-9a2</div><div className="s">params hash 0x7e3a · 14 deltas vs base</div></div></div>
            <div className="step done"><div className="dot" /><div className="body"><div className="h">Backtest · 18mo walk-forward</div><div className="s">window 90d · step 7d · 1,247 trades</div></div></div>
            <div className="step done"><div className="dot" /><div className="body"><div className="h">Artifacts · 14 files</div><div className="s">equity · trades · pnl · slippage · 11 more</div></div></div>
            <div className="step done"><div className="dot" /><div className="body"><div className="h">Verdict · pass</div><div className="s">all 6 gates · evidence pack v2</div></div></div>
            <div className="step active"><div className="dot" /><div className="body"><div className="h">D.2 promotion · pending review</div><div className="s">queued · awaiting operator on desktop</div></div></div>
            <div className="step pending"><div className="dot" /><div className="body"><div className="h">Paper handoff</div><div className="s">scheduled after D.2 approval</div></div></div>
          </div>
        </div>

        <ReadOnly msg="Promotion decisions are signed on Desktop" />
      </div>
      <TabBar active={tab} onPick={setTab} />
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// SCREEN 4 — Alerts / Corridor
// ═════════════════════════════════════════════════════════════════════
function AlertsScreen({ tab = 'alert', setTab }) {
  return (
    <div className="m-screen">
      <StatusBar />
      <Header eyebrow="Notifications" title="Alerts" />
      <Strip cells={[
        { k: 'Open', v: '4', tone: 'warn' },
        { k: 'Today', v: '17', tone: '' },
        { k: 'Acked', v: '13', tone: 'ok' },
      ]} />
      <div className="m-body">
        <div className="m-card elev">
          <div className="m-sec" style={{ margin: 0 }}>
            <span className="label">Corridor · live</span>
            <span className="count">window 60m</span>
          </div>
          <div style={{ marginTop: 8 }}>
            <Sparkline pts={[1, 1.1, 0.9, 1.0, 1.2, 1.4, 1.6, 1.5, 1.8, 2.1, 1.9, 1.8, 2.1]} tone="warn" />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)' }}>
            <span>liquidity · z-score</span>
            <span style={{ color: 'var(--warn)' }}>2.1 σ · hold</span>
          </div>
        </div>

        <div className="m-sec"><span className="label">Open · 4</span><span className="count">tap to inspect</span></div>
        {MOBILE_DATA.alerts.map((a, i) => (
          <div key={i} className={`m-alert ${a.lvl}`}>
            <div className="bar" />
            <div className="body">
              <div className="h">{a.h}</div>
              <div className="s">{a.s}</div>
            </div>
            <div className="meta">{a.t}</div>
          </div>
        ))}
      </div>
      <TabBar active={tab} onPick={setTab} />
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// SCREEN 5 — Promotion Gate (D.2/D.3)
// ═════════════════════════════════════════════════════════════════════
function GateScreen({ tab = 'gate', setTab }) {
  return (
    <div className="m-screen">
      <StatusBar />
      <Header eyebrow="Decision" title="Promotion Gate" />
      <Strip cells={[
        { k: 'In Lab', v: '24', tone: '' },
        { k: 'D.2', v: '5', tone: '' },
        { k: 'D.3', v: '2', tone: 'ok' },
      ]} />
      <div className="m-body">
        <div className="m-card elev">
          <div className="m-sec" style={{ margin: 0 }}><span className="label">Active candidate</span><span className="count">awaits sign-off</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: 10 }}>
            <div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--muted)', letterSpacing: '0.10em' }}>r-7a3f</div>
              <div style={{ fontSize: 16, fontWeight: 600, marginTop: 2 }}>momentum-15m · v0.42</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>queued 01:14 · 8h 27m ago</div>
            </div>
            <span className="m-badge cand">D.2 → D.3</span>
          </div>
        </div>

        <div className="m-sec"><span className="label">Gate stages</span><span className="count">6 of 7</span></div>
        <div className="m-card" style={{ padding: '4px 14px' }}>
          <div className="m-gate">
            <div className="lane pass"><div className="badge"><Icon k="check" size={16} /></div><div className="meta"><div className="h">L.1 · Lab backtest<span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--success)' }}>passed</span></div><div className="s">walk-forward 18mo · Sharpe 1.82</div></div></div>
            <div className="lane pass"><div className="badge"><Icon k="check" size={16} /></div><div className="meta"><div className="h">L.2 · Variance gate<span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--success)' }}>passed</span></div><div className="s">σ stable across 6 folds</div></div></div>
            <div className="lane pass"><div className="badge"><Icon k="check" size={16} /></div><div className="meta"><div className="h">D.1 · Evidence pack<span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--success)' }}>verified</span></div><div className="s">14 artifacts · hash 0x7e3a</div></div></div>
            <div className="lane gate"><div className="badge">D.2</div><div className="meta"><div className="h">D.2 · Operator review<span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent)' }}>awaiting</span></div><div className="s">desktop sign-off required</div></div></div>
            <div className="lane"><div className="badge">D.3</div><div className="meta"><div className="h">D.3 · Paper handoff<span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)' }}>blocked</span></div><div className="s">14-day supervised paper</div></div></div>
            <div className="lane"><div className="badge">P.1</div><div className="meta"><div className="h">P.1 · Production<span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)' }}>locked</span></div><div className="s">requires D.3 closure</div></div></div>
          </div>
        </div>

        <ReadOnly msg="View only · Approve from Desktop · operator-only" />
      </div>
      <TabBar active={tab} onPick={setTab} />
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// SCREEN 6 — Artifact summary
// ═════════════════════════════════════════════════════════════════════
function ArtifactScreen({ tab = 'runs', setTab }) {
  const arts = [
    { kind: 'EQ', name: 'equity.parquet', size: '2.4 MB', meta: '1,247 rows · 18mo' },
    { kind: 'TR', name: 'trades.parquet', size: '4.1 MB', meta: '1,247 trades · ledger' },
    { kind: 'PD', name: 'pnl-daily.parquet', size: '180 KB', meta: '540 rows · daily' },
    { kind: 'SL', name: 'slippage.csv', size: '92 KB', meta: 'bps · realized vs theo' },
    { kind: 'CF', name: 'config.lock.yaml', size: '6 KB', meta: 'frozen params · hash 0x7e3a' },
    { kind: 'LG', name: 'engine.log', size: '14 MB', meta: '4h 12m · structured' },
    { kind: 'PR', name: 'profile.json', size: '38 KB', meta: 'fold-by-fold metrics' },
  ];
  return (
    <div className="m-screen">
      <StatusBar />
      <div style={{ padding: '12px 16px 10px', borderBottom: '1px solid var(--line-soft)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <button style={{ color: 'var(--muted)' }}><Icon k="chev" size={20} color="var(--muted)" /></button>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.10em', color: 'var(--muted)' }}>r-7a3f · artifacts</div>
          <div style={{ fontSize: 17, fontWeight: 600, marginTop: 2 }}>Evidence pack</div>
        </div>
        <span className="m-badge neut">14 files</span>
      </div>
      <div className="m-body">
        <div className="m-card elev">
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div className="m-bigmetric"><span className="v">22.4<span style={{ fontSize: 14, color: 'var(--muted)' }}> MB</span></span><span className="d">Total · 14 files · verified</span></div>
            <div style={{ textAlign: 'right' }}>
              <div className="k" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--muted)', letterSpacing: '0.10em', textTransform: 'uppercase' }}>Hash</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent)', marginTop: 2 }}>0x7e3a…f81b</div>
            </div>
          </div>
        </div>

        <div className="m-sec"><span className="label">Files</span><span className="count">grouped by lineage</span></div>
        <div className="m-list">
          {arts.map((a, i) => (
            <div key={i} className="row" style={{ alignItems: 'flex-start' }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', flex: 1 }}>
                <div className="m-glyph">{a.kind}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{a.name}</div>
                  <div className="sub">{a.meta}</div>
                </div>
              </div>
              <div className="val">{a.size}</div>
            </div>
          ))}
        </div>

        <ReadOnly msg="Summaries only · full artifact inspection on Desktop" />
      </div>
      <TabBar active={tab} onPick={setTab} />
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// SCREEN 7 — Assistant / Notes
// ═════════════════════════════════════════════════════════════════════
function AssistantScreen({ tab = 'more', setTab }) {
  return (
    <div className="m-screen">
      <StatusBar />
      <Header eyebrow="Companion" title="Assistant" />
      <Strip cells={[
        { k: 'Mode', v: 'Advisory', tone: 'ok' },
        { k: 'Context', v: 'r-7a3f', tone: '' },
        { k: 'Scope', v: 'Read', tone: '' },
      ]} />
      <div className="m-body" style={{ gap: 14 }}>
        <div className="m-msg asst">
          <div className="bubble">Run <span className="mono" style={{ color: 'var(--accent)' }}>r-7a3f</span> passed all 6 lab gates and is queued for D.2 review. Variance is stable across the 6 walk-forward folds.</div>
          <div className="meta">Assistant · 08:42</div>
        </div>
        <div className="m-msg ops">
          <div className="bubble">Why is corridor on hold?</div>
          <div className="meta">Operator · 09:18</div>
        </div>
        <div className="m-msg asst">
          <div className="bubble">Liquidity z-score on maker-5m crossed 2.0 σ at 00:48. The desk paused new entries — existing positions are intact. Recommended action: review on Desktop before resuming.</div>
          <div className="meta">Assistant · 09:18</div>
        </div>
        <div className="m-msg ops">
          <div className="bubble">Pin to evidence: r-7a3f · "needs supervised paper before D.3"</div>
          <div className="meta">Operator note · 09:22</div>
        </div>
        <div className="m-msg asst">
          <div className="bubble">Note attached to r-7a3f evidence pack. Visible to Desktop reviewers.</div>
          <div className="meta">Assistant · 09:22</div>
        </div>
      </div>
      <div style={{ padding: '8px 16px 6px', borderTop: '1px solid var(--line-soft)', background: 'var(--ink-800)' }}>
        <div style={{ background: 'var(--ink-700)', border: '1px solid var(--line)', borderRadius: 12, padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--muted)', display: 'flex', justifyContent: 'space-between' }}>
          <span>Ask · pin a note · summarize</span>
          <span style={{ color: 'var(--muted-dark)' }}>read-only</span>
        </div>
      </div>
      <TabBar active={tab} onPick={setTab} />
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// SCREEN 8 — Settings / safety boundaries
// ═════════════════════════════════════════════════════════════════════
function SettingsScreen({ tab = 'more', setTab }) {
  return (
    <div className="m-screen">
      <StatusBar />
      <Header eyebrow="Companion" title="Settings" />
      <div className="m-body">
        <div className="m-sec" style={{ margin: '0 2px -4px' }}><span className="label">Identity</span></div>
        <div className="m-list">
          <div className="row"><div><div className="label">Workstation</div><div className="sub">QL-DESK-01 · LAN paired</div></div><span className="val">paired</span></div>
          <div className="row"><div><div className="label">Operator</div><div className="sub">signed via desktop key</div></div><span className="val">ops-04</span></div>
          <div className="row"><div><div className="label">Session scope</div><div className="sub">expires 18:00 UTC</div></div><span className="val">read</span></div>
        </div>

        <div className="m-sec"><span className="label">Notifications</span></div>
        <div className="m-list">
          <div className="row"><div className="label">Promotion gate events</div><span className="val" style={{ color: 'var(--accent)' }}>on</span></div>
          <div className="row"><div className="label">Corridor drift ≥ 1.5σ</div><span className="val" style={{ color: 'var(--accent)' }}>on</span></div>
          <div className="row"><div className="label">Reachability degraded</div><span className="val" style={{ color: 'var(--accent)' }}>on</span></div>
          <div className="row"><div className="label">Run completion</div><span className="val">off</span></div>
        </div>

        <div className="m-sec"><span className="label">Safety boundaries · enforced</span></div>
        <div className="m-list">
          <div className="row disabled"><div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}><Icon k="lock" size={16} color="var(--muted-dark)" /><div><div className="label">Submit broker orders</div><div className="sub">desktop · operator key required</div></div></div><span className="val lock">locked</span></div>
          <div className="row disabled"><div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}><Icon k="lock" size={16} color="var(--muted-dark)" /><div><div className="label">Approve D.2 / D.3</div><div className="sub">supervised on desktop</div></div></div><span className="val lock">locked</span></div>
          <div className="row disabled"><div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}><Icon k="lock" size={16} color="var(--muted-dark)" /><div><div className="label">Modify configs</div><div className="sub">artifact integrity</div></div></div><span className="val lock">locked</span></div>
          <div className="row disabled"><div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}><Icon k="lock" size={16} color="var(--muted-dark)" /><div><div className="label">Start / stop runs</div><div className="sub">execution authority</div></div></div><span className="val lock">locked</span></div>
        </div>

        <ReadOnly msg="Companion is review-only by design · architectural rule" />
      </div>
      <TabBar active={tab} onPick={setTab} />
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════
// INTERACTIVE PROTOTYPE — bottom tabs cycle screens
// ═════════════════════════════════════════════════════════════════════
function InteractivePrototype() {
  const [tab, setTab] = useState('home');
  const map = {
    home: HomeScreen,
    runs: RunsScreen,
    alert: AlertsScreen,
    gate: GateScreen,
    more: SettingsScreen,
  };
  const Cmp = map[tab];
  return <Cmp tab={tab} setTab={setTab} />;
}

Object.assign(window, {
  HomeScreen, RunsScreen, RunDetailScreen, AlertsScreen,
  GateScreen, ArtifactScreen, AssistantScreen, SettingsScreen,
  InteractivePrototype,
});
