# QuantLab Desktop

This directory contains the first desktop shell for QuantLab.

Current scope:

- Electron-based shell
- auto-starts `research_ui/server.py`
- workstation-first sidebar and shell chrome
- primary `Launch` workspace plus native operator surfaces (`Runs`, `Compare`, `Candidates`, `Paper Ops`, `System`, `Experiments`, `Assistant`)
- local decision store for candidates, shortlist, and baseline
- context tabs that combine shell-native workstation surfaces with transitional launch/job continuity
- runtime strip for QuantLab workspace visibility

This is intentionally a first block, not the final product shell.

## Desktop v1 Runtime State

Desktop v1 is a functional operator workstation with explicit transitional boundaries.

- React is the default runtime for Desktop.
- React is the sole renderer. Legacy renderer (`app-legacy.js`, `legacy.html`) has been removed.
- Legacy rollback via `start:legacy` / `QUANTLAB_DESKTOP_RENDERER=legacy` has been removed. Rollback now requires reverting this PR or restoring the removed legacy renderer files from Git history.
- `npm start` builds and starts Desktop with the React renderer.
- `research_ui` remains a transitional API and reachability boundary; it is not the target shell or canonical workspace surface.

This keeps Desktop v1 honest: the product can ship as a usable operator workstation while the React migration continues through narrow slices.

## Start

From the repository root:

```powershell
cd desktop
npm ci
npm start
```

`desktop/package-lock.json` is intentionally committed. Use `npm ci` for
reproducible installs; update the lockfile only when `desktop/package.json`
changes or an explicit dependency-policy issue requires it.

Smoke check:

```powershell
cd desktop
npm run smoke
```

React parity gate (promotion proof):

```powershell
cd desktop
npm run smoke:fallback
```

Gate definition: [`docs/desktop-react-parity-gate.md`](../docs/desktop-react-parity-gate.md)

> **Note:** `smoke:react:fallback`, `smoke:legacy:*`, and `smoke:renderer-rollout` aliases have been removed. `npm run smoke` and `npm run smoke:fallback` are the canonical smoke commands.

## Cursor MCP

This folder also exposes a local MCP server for Cursor via [`.cursor/mcp.json`](../.cursor/mcp.json).

Available tools:

- `quantlab_check`
- `quantlab_version`
- `quantlab_runs_list`
- `quantlab_paper_sessions_health`
- `quantlab_desktop_smoke`
- `quantlab_read_file`
- `quantlab_outputs_list`
- `quantlab_artifact_read`

`quantlab_outputs_list` accepts optional `relative_path` and `entry_kind` filters (`all`, `directory`, `file`).

The server entrypoint is `mcp-server.mjs`, and the `mcp` npm script runs it directly.

## Current Surfaces

- System
- Experiments and Sweep Handoff
- Launch
- Runs, Run Detail, and Artifacts
- Candidates
- Compare
- Paper Ops
- Launch Review
- Assistant support lane

## Notes

- The assistant support lane is deterministic and specialized for QuantLab commands.
- External assistant adapters have been removed from Desktop. Future assistant work must be QuantLab-owned and explicitly scoped.
- React default runtime, broad legacy removal, and full Launch ownership are post-v1 unless a later issue resolves the remaining operator-flow boundary explicitly.
- The renderer is now split into focused ES modules under `desktop/renderer/modules/` so workflow logic, decision-store helpers, and tab renderers no longer live in one file.
- The shell can now review recent launch jobs and explain the latest failure from local stdout/stderr logs.
- The shell now persists decision state locally in `outputs/desktop/candidates_shortlist.json`.
- The shell now prefers `Launch` on startup so execution and queue review stay primary, while `Runs`/`System` remain one click away.
- `Run`, `Compare`, `Artifacts`, `Candidates`, and `Paper Ops` are now shell-native tabs designed to support launch -> inspect -> compare -> decide continuity.
- `Experiments` is now a shell-native workspace for local sweep configs and recent sweep outputs under `configs/experiments` and `outputs/sweeps`.
- Sweep rows can now be tracked, shortlisted, baselined, and compared in a local handoff layer persisted in `outputs/desktop/sweep_decision_handoff.json`.
- The shell now restores lightweight workspace context from `outputs/desktop/workspace_state.json`, including tabs, active context, selected runs, and launch form inputs.
