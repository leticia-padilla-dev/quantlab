# QuantLab — Claude Code working guide

## Project structure

```
quantlab/
├── src/quantlab/          # Python core (backtest, broker, CLI, strategies)
│   ├── brokers/           # boundary.py, hyperliquid.py, kraken.py
│   ├── cli/               # app_args.py, broker_preflight.py
│   └── ...
├── desktop/               # Electron desktop app
│   └── renderer/
│       ├── components/    # React TSX/JSX surfaces
│       ├── hooks/         # Native React hooks (no legacy dependency)
│       ├── modules/       # utils.js, decision-store.js, etc.
│       └── app-legacy.js  # Legacy renderer — behavioral reference, DO NOT MODIFY
├── test/                  # Python tests (pytest)
├── docs/                  # Runbooks and architecture docs
└── main.py                # CLI entry point
```

## Validation commands

### Python core
```bash
PYTHONPATH=src pytest test/ -q                          # full suite
PYTHONPATH=src pytest test/test_hyperliquid_broker_adapter.py -q   # broker only
```

### Desktop
```bash
cd desktop && npm run typecheck   # TypeScript — must pass before any commit
cd desktop && npm run build       # Vite build — must pass before any commit
npm run smoke:react:fallback      # React fallback smoke
npm run smoke:react:real-path     # React real-path smoke
```

## Git workflow — non-negotiable rules

1. **Always create a new branch before touching any file.** Never commit directly to `main`.
2. **Branch naming:** `feat/`, `fix/`, `docs/` prefixes. Descriptive slug.
3. **Push with:** `git push -u origin <branch-name>`
4. **Open a PR** after pushing. Use draft only when the slice is incomplete, risky, or intentionally waiting for review.
5. **Merge only after CI green.** Check with `gh pr checks <number>`.
6. **After merge:** `git checkout main && git pull origin main`

The direct-to-main exception that happened in Slice B (#410) must not be repeated.

## Desktop renderer architecture

### Two renderers — React is default, legacy is deprecated fallback

| Mode | Command | Status |
|------|---------|--------|
| React | `npm start` or `npm run start:react` | Default renderer |
| Legacy | `npm run start:legacy` | Deprecated fallback / continuity path |

**Legacy renderer is in `deprecated-fallback` mode as of 2026-05-05. It receives no new features.**
`npm run start:legacy` remains available as an operator escape hatch until native parity is confirmed.

**Do not retire legacy or remove rollback support yet. Final removal (#529) is blocked by remaining parity/contract decisions:**
- #525 run-related jobs correlation (if still needed)
- #526 backend/producer contract (if still needed)
- #527 sweep decision accessors (if active)

### Legacy is behavioral reference, not architectural truth

When implementing native React hydration, mirror the *user-visible behavior* of the legacy equivalent. Do not copy legacy architecture, monolithic patterns, or global state design into React. Legacy must not be treated as architectural truth.

*Note: Visible jobs accessors (Launch jobs, failed jobs) were migrated in #524/#530 to native React accessors.*

### Native hook wiring pattern

Every native hook follows this pattern — no exceptions:

```ts
// Pass null/false to disable the hook when legacy has already hydrated
const native = useHook(state.X != null ? null : param);
const effective = state.X ?? native.value ?? fallback;
```

Established hooks and what they mirror:

| Hook | Legacy mirror | Disable condition |
|------|--------------|-------------------|
| `useRunDetail(runId, run)` | `loadRunDetail()` | `tab.detail != null ? null : runId` |
| `useSnapshot(serverUrl)` | `refreshSnapshot()` | `state.snapshot != null ? null : serverUrl` |
| `useExperimentsWorkspace(enabled)` | `buildExperimentsWorkspace()` | `!Boolean(state.experimentsWorkspace)` |

### QuantLabContext state ownership

| State | Owner | Notes |
|-------|-------|-------|
| `tabs`, `activeTabId`, `selectedRunIds` | QuantLabContext (React) | Persisted via bridge |
| `candidatesStore` | Legacy global | Bridged read + write actions |
| `sweepDecisionStore` | Legacy global | Bridged read; write actions partially bridged |
| `snapshot`, `experimentsWorkspace` | Legacy global / native hook | Native fallback when legacy absent |

### Bridged actions (available in `ctx`)

**Candidates:** `setBaseline`, `toggleCandidate`, `toggleShortlist`
**Decision read:** `decision.isBaselineRun`, `decision.isCandidateRun`, `decision.getCandidateEntriesResolved`, etc.

**Not yet bridged (known gap):** `toggleSweepEntry`, `toggleSweepShortlist`, `setSweepBaseline`, `findSweepDecisionRow`, `refresh`

## Files that are out of scope by default

Unless a task explicitly targets one of these, never modify them:

- `desktop/renderer/app-legacy.js` — legacy renderer, behavioral reference only
- `desktop/main/*` — Electron main process and IPC channels
- `desktop/shared/ipc/channels.ts` — IPC channel definitions
- `desktop/main/smoke-service.js` — smoke test infrastructure
- `src/quantlab/brokers/hyperliquid.py` — only touch for Hyperliquid-specific broker fixes
- `src/quantlab/brokers/boundary.py` — only touch for execution safety boundary changes

## Broker / execution rules

- **Never submit live orders without explicit `apruebo submit` from the user.**
- Hyperliquid signed actions can be generated freely; submission requires approval.
- `dry_run=True` is the default and must remain default unless explicitly overridden.
- Broker rendering in the desktop must remain generic — no Hyperliquid-specific field names in UI components.

## Python broker: known behavioral contracts

- Price quantization: 5 sig figs, `ROUND_UP` for buy, `ROUND_DOWN` for sell
- IOC price buffer: buy = best_ask + 5 bps, sell = best_bid - 5 bps, then quantized
- Min order value: `_HYPERLIQUID_MIN_ORDER_VALUE_USD = Decimal("10")`
- `reduce_only` is wired through `ExecutionIntent` → action payload `"r"` field

## Smoke selectors — never remove

Each surface component has a `data-smoke` attribute that must be preserved:

| Component | Selector |
|-----------|----------|
| `PaperOpsPane` | `data-smoke="surface-paper-ops"` |
| `SystemPane` | `data-smoke="surface-system"` |
| `ExperimentsPane` | `data-smoke="surface-experiments"` |
| `RunDetailPane` | `.run-detail-shell`, `.artifact-list`, `.tab-placeholder` |

## IPC bridge methods available to hooks

```js
window.quantlabDesktop.listDirectory(path, depth)
window.quantlabDesktop.readProjectJson(path)
window.quantlabDesktop.readProjectText(path)
window.quantlabDesktop.requestJson(relativePath)   // HTTP to local server
window.quantlabDesktop.openPath(path)
window.quantlabDesktop.openExternal(url)
window.quantlabDesktop.postJson(path, body)
```

Do not introduce new IPC channels without explicit approval.
