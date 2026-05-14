# Hyperliquid: Submit Alert Horizon Policy

Issue: [#802](https://github.com/Whiteks1/quantlab/issues/802)  
Refs: [#800](https://github.com/Whiteks1/quantlab/issues/800)

Status: policy-only. docs-only. No runtime changes. Stage E remains blocked.

## Objective

Define a deterministic policy for interpreting Hyperliquid submit alerts with an explicit horizon.

This policy separates:

- historical evidence (preserved and auditable)
- current operational go/no-go window (blocks execution)

so the system does not remain blocked forever by old rejections while still refusing to proceed under current critical posture.

## Scope / Constraints

```yaml
scope:
  policy_only: true
  docs_only: true
  runtime_changes: false
  automation: false
  stage_e: blocked
  outputs_versioned: false
```

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Inputs (Artifacts)

Canonical root:

```text
outputs/hyperliquid_submits/
```

Primary inputs:

- `outputs/hyperliquid_submits/hyperliquid_submits_alerts.json`
- `outputs/hyperliquid_submits/hyperliquid_submits_health.json`

Supporting per-session evidence:

- `outputs/hyperliquid_submits/<session_id>/session_status.json`
- `outputs/hyperliquid_submits/<session_id>/hyperliquid_submit_response.json`
- `outputs/hyperliquid_submits/<session_id>/hyperliquid_reconciliation.json`
- `outputs/hyperliquid_submits/<session_id>/hyperliquid_order_status.json`
- `outputs/hyperliquid_submits/<session_id>/hyperliquid_fill_summary.json`

## Definitions

```yaml
definitions:
  historical:
    description: "Evidence outside the declared current window."
    preserved: true
    blocks_forever: false
  current_window:
    description: "Evidence inside the declared go/no-go horizon window."
    blocks_go_no_go_if_critical: true
```

## Required Policy Semantics (Non-Negotiable)

```yaml
historical_critical:
  preserved: true
  blocks_forever: false

current_window_critical:
  blocks_go_no_go: true

hard_freeze_even_if_historical:
  - reconciliation_ambiguity
  - missing_identifiers
  - unresolved_open_exposure
  - artifact_corruption
  - unknown_terminal_state
```

## Current Window Specification

This policy supports two orthogonal horizon definitions.

The operator must declare the horizon being used for the current go/no-go decision.

```yaml
horizon:
  by_days:
    window_days: <fill>
    now_reference: "operator_now"
  by_sessions:
    window_sessions: <fill>
    ordering: "by activity_at descending"
```

Notes:
- The horizon is an operator-declared interpretation layer.
- This policy does not modify artifacts, alerts, or runtime behavior.
- The root historical alert posture remains preserved and visible.

## Deterministic Evaluation Procedure (Docs-Only)

### Step 1 — Read Root Posture (Historical + Current)

Read:

- `hyperliquid_submits_alerts.json.alert_status`
- `hyperliquid_submits_alerts.json.alert_counts`
- `hyperliquid_submits_alerts.json.latest_alert_*`

Interpretation:
- This is the historical posture across all sessions.
- It is evidence, not a current-window go/no-go decision by itself.

### Step 2 — Derive Current Window Set

From `hyperliquid_submits_alerts.json.alerts[]`, select sessions in the current window using one of:

- `by_days`: `activity_at >= now - window_days`
- `by_sessions`: take top `window_sessions` by `activity_at`

Record the chosen window in the operator memo.

### Step 3 — Compute Current Window Alert Status

Compute:

```yaml
current_window_alert_status:
  critical_if_any_critical_in_window: true
  warning_if_any_warning_in_window: true
  ok_only_if_no_alerts_in_window: true
```

Decision:
- If `current_window_alert_status == critical`: NO_GO (stop/freeze/no-new-session).
- If `current_window_alert_status != critical`: continue to Step 4 (hard-freeze scan).

### Step 4 — Hard-Freeze Scan (Always Blocks)

Even if the critical evidence is historical, hard-freeze applies if any of these are true for any session (historical or current):

- reconciliation ambiguity or `reconciliation_required`
- remote identifiers missing after submit
- unresolved open exposure
- artifacts missing or corrupted such that terminality cannot be proven

Operator rule:
- If any hard-freeze is present: NO_GO (stop/freeze/no-new-session).

### Step 5 — Governance Outcome

```yaml
go_no_go:
  if_current_window_critical: NO_GO
  if_hard_freeze_present: NO_GO
  else: GO (for a single supervised session only, under the D.3 micro-runtime procedure)
```

## Evidence Preservation Rules

```yaml
evidence_preservation:
  forbidden:
    - delete_historical_alerts
    - rewrite_alert_artifacts
    - hide_rejected_sessions
  required:
    - keep_root_historical_alert_status_visible
    - compute_current_window_status_as_additive_overlay
```

## Relationship to #800 (Micro-Runtime Cycle)

Until this policy exists and is applied, the micro-runtime cycle remains blocked:

```yaml
issue_800:
  decision: NO_GO
  blocked_by:
    - policy_not_defined_or_not_applied
```

## References

- [hyperliquid-submit-session-evidence-contract.md](./hyperliquid-submit-session-evidence-contract.md)
- [d3-micro-runtime-supervision-slice.md](./d3-micro-runtime-supervision-slice.md)
- [d3-reconciliation-walkthrough.md](./d3-reconciliation-walkthrough.md)
- [stage-e-runtime-slice-policy.md](./stage-e-runtime-slice-policy.md)
- [d3-2026-05-14-micro-runtime-blocked-by-historical-hyperliquid-alerts.md](./d3-2026-05-14-micro-runtime-blocked-by-historical-hyperliquid-alerts.md)

## Non-Goals

- This policy does not change runtime behavior.
- This policy does not authorize submit automation.
- This policy does not open Stage E.
