# Desktop React Functional Parity Evidence

Date: 2026-05-04

## Purpose

This document records the current evidence for Desktop React functional parity against the Legacy shell.

React is now capable of exercising the core operator loop, but this document does not declare React as the default shell. Default promotion remains gated by the explicit readiness checklist below.

## Enabling PRs Merged Into `main`

| PR | Title | Parity contribution |
| --- | --- | --- |
| #507 | `fix(desktop): bridge sweep decision actions into QuantLabContext` | Exposed sweep decision actions needed by React Experiments surfaces. |
| #508 | `desktop(react): own candidates store in QuantLabContext` | Moved Candidates ownership into React while preserving persistence semantics. |
| #509 | `desktop(react): add operator recovery actions for empty runs state` | Made the empty Runs state actionable for operators. |
| #510 | `desktop(react): make Launch quick-start usable with existing configs` | Added config selection for Quick Launch using existing experiment configs. |
| #511 | `desktop(react): surface data-source diagnostics across System/Runs/Launch` | Added backend and runs-index diagnostics across the operator path. |

## Related Active PRs

| PR | Title | Status | Relevance |
| --- | --- | --- | --- |
| #513 | `desktop(react): wire manual registry refresh into RunsPane` | Draft | Related to explicit React registry refresh behavior. |
| #514 | `tools: add React Desktop dev start helper` | Open | Adds a reliable React startup helper to avoid confusing React and Legacy verification. |

## Operational Evidence

The following operator loop has been exercised with the ETH experiment configuration and the local research backend:

- Backend started with `QUANTLAB_LOCAL_API_TOKEN`.
- `outputs/runs/runs_index.json` generated through the canonical run-index writer.
- Sweep launched from the Desktop flow using `configs/experiments/eth_2023_grid.yaml`.
- The generated run was indexed and exposed with real metrics.
- Candidate marking and decision queue behavior were exercised.
- Compare was exercised with two runs.

## Legacy vs React Evidence Matrix

| Step | Legacy | React | Evidence state |
| --- | --- | --- | --- |
| Start with backend attached | Validated | Validated | Runtime Live / research surface ready observed. |
| Quick Launch with config selection | Validated | Validated | `eth_2023_grid.yaml` selectable from launch flow. |
| Submit sweep | Validated | Validated | Sweep launch accepted and completed. |
| Runs visible from index | Validated | Validated | Indexed runs visible with real metrics. |
| Mark Candidate | Validated | Validated | Candidates count and decision queue updated. |
| Candidates surface | Validated | Validated | Candidate queue visible. |
| Compare two runs | Validated | Validated | Comparative table visible. |
| Open run detail | Validated | Pending explicit React evidence | Requires final click-through confirmation in React. |
| Open artifacts | Validated | Pending explicit React evidence | Requires final click-through confirmation in React. |

## Known Non-Blocking Gap

React currently has a visual diagnostic mismatch in at least one operator path:

- Runs and/or Launch may show `Backend: Offline` even when the backend is reachable and the workflow can proceed.

This is a display-state bug, not a launch blocker. It must still be fixed before React is considered default-ready because it can mislead the operator.

## Default-Readiness Checklist

React must not become the default Desktop shell until all of the following are true:

- [ ] Backend status indicators agree with the actual `workspaceState.serverUrl` / runtime state.
- [ ] React `Open run` is explicitly verified against a real indexed run.
- [ ] React `Artifacts` is explicitly verified against a real indexed run.
- [ ] Candidate marking and persistence survive refresh/restart.
- [ ] Compare can be opened from selected or shortlisted React state.
- [ ] `npm run smoke:react:fallback` is green.
- [ ] `npm run smoke:react:real-path` is green.
- [ ] `npm run smoke:legacy:fallback` is green.
- [ ] No new IPC channel, backend behavior, or legacy deletion is required for the parity proof.

## Current Assessment

React has enough functional evidence to continue the operator-parity track. It is no longer merely architectural scaffolding.

The remaining work is not broad migration. It is narrow readiness hardening:

1. Fix the backend diagnostic mismatch.
2. Capture explicit React evidence for run detail and artifacts.
3. Close the binary default-readiness gate.

Until then, Legacy remains the safest default operator shell, and React remains the active candidate shell.
