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
│       └── app-legacy.js  # REMOVED in #529 — legacy renderer has been deleted
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
npm run smoke:fallback          # React fallback smoke (canonical)
npm run smoke:real-path         # React real-path smoke
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

### React is the sole renderer (Legacy removed in #529)

The Legacy renderer (`app-legacy.js`, `legacy.html`, `start:legacy`) was removed in #529 after full native parity was confirmed. React is now the only renderer path.

| Mode | Command | Status |
|------|---------|--------|
| React | `npm start` | Sole renderer |

**Legacy rollback** now requires reverting #529 or restoring removed files from Git history.

*Note: Visible jobs accessors (Launch jobs, failed jobs) were migrated in #524/#530 to native React accessors.*

### Native hook wiring pattern

Every native hook follows this pattern — no exceptions:

```ts
// Pass null/false to disable the hook when legacy has already hydrated
const native = useHook(state.X != null ? null : param);
const effective = state.X ?? native.value ?? fallback;
```

Established hooks and what they mirror:

| Hook | Purpose |
|------|---------|
| `useRunDetail(runId, run)` | Loads run detail via IPC |
| `useSnapshot(serverUrl)` | Polls native API snapshot |
| `useExperimentsWorkspace(enabled)` | Loads experiments workspace natively |

### QuantLabContext state ownership

| State | Owner | Notes |
|-------|-------|-------|
| `tabs`, `activeTabId`, `selectedRunIds` | QuantLabContext (React) | Persisted via IPC bridge |
| `candidatesStore` | `useCandidatesStore` (native) | Persisted locally |
| `sweepDecisionStore` | `useSweepDecisionStore` (native) | Persisted locally |
| `snapshot` | `useSnapshot` (native) | Polled from local API |

**All legacy global state accessors have been removed.** The context is fully native.

## Files that are out of scope by default

Unless a task explicitly targets one of these, never modify them:

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
