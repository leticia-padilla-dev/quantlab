# Desktop React Ownership Map

**Purpose:** map current React-owned state and remaining legacy dependencies before
cutting any `research_ui` or legacy renderer boundary.

This document is an ownership map, not a migration backlog. It supports the
next Desktop cleanup decisions and the eventual `#412` legacy retirement path.

## Current React-Owned State

React now owns the active workstation shell:

- tab list, active tab, selected runs, and shell persistence through
  `QuantLabContext`
- run registry through `RegistryContext`
- Run Detail hydration through `useRunDetail`
- Paper Ops and System health hydration through `useSnapshot`
- Experiments workspace hydration through `useExperimentsWorkspace`
- native surfaces for Runs, Run Detail, Artifacts, Candidates, Compare, Paper
  Ops, System, Experiments, Launch, Job Review, and Assistant

The React shell is the target Desktop architecture. Legacy remains a behavioral
continuity reference, not architectural truth.

## Legacy-Backed Dependencies

The React shell still merges selected legacy state and delegates selected actions
through the legacy bridge:

| Dependency | Current owner | React consumer | Cut risk |
| --- | --- | --- | --- |
| `candidatesStore` | legacy/global state | Runs, Run Detail, Candidates, Compare, Paper Ops, System | high |
| `snapshot` fallback | legacy/global state | Runs, Paper Ops, System, Launch | medium |
| `experimentsWorkspace` fallback | legacy/global state | Experiments | low |
| `getJobs` | legacy accessor | Paper Ops, System, Launch | high |
| `getLatestFailedJob` | legacy accessor | Paper Ops, System, Launch | medium |
| `loadRunDetail` | legacy accessor | Compare | medium |
| `getRunRelatedJobs` | legacy accessor | Run Detail | medium |
| `getSweepDecisionEntriesForRun` | legacy accessor | Run Detail | medium |
| `setBaseline` | legacy action | Runs, Run Detail, Candidates, Compare | high |
| `toggleCandidate` | legacy action | Runs, Run Detail, Candidates, Compare | high |
| `toggleShortlist` | legacy action | Run Detail, Candidates, Compare | high |

These dependencies are allowed while React reaches parity, but they should not
grow. New React work should not add new direct global legacy accessors.

## `research_ui` Boundary Still Required

`research_ui` remains a transitional external API boundary for:

- local server reachability and real-path Desktop smoke
- `requestJson` and `postJson` API paths used by native React surfaces
- `/api/launch-control` for Launch and job submission
- paper and broker health endpoints used by `useSnapshot`
- browser bridge links from Launch, Paper Ops, and System

`research_ui` is not product authority. It is currently an API/reachability
boundary and a continuity bridge while native ownership is completed.

## `#412` Retirement Blockers

Do not retire the legacy renderer or remove `research_ui` support until:

- `candidatesStore` and decision actions are React-owned
- job and launch accessors no longer depend on legacy globals
- Run Detail related-job lookup is React/native-owned
- Compare no longer depends on legacy `loadRunDetail`
- snapshot and experiments fallbacks are either removed or explicitly retained
  as external compatibility boundaries
- real-path smoke has a non-legacy path for the required server/API assertions

`#412` should remain a controlled cleanup slice, not broad deletion.

## Recommended Cut Order

1. Move `candidatesStore` and decision actions out of legacy globals.
2. Replace job and launch accessors with a native launch-control model.
3. Replace Run Detail related-job lookup.
4. Replace Compare `loadRunDetail` usage with a native loader path.
5. Remove or explicitly retain snapshot and experiments legacy fallbacks.

Each cut should be a separate branch and PR from fresh `main`.
