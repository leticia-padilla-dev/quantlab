# D.3 Issue #800 — GO Re-evaluation Window (Policy Memo)

Issue: [#804](https://github.com/Whiteks1/quantlab/issues/804)  
Refs: [#800](https://github.com/Whiteks1/quantlab/issues/800)

Status: docs-only policy memo. No runtime changes. No submit authorized. Stage E remains blocked.

## Purpose

Fix a concrete, non-ambiguous go/no-go window for D.3 Issue #800.

This prevents a “policy exists but application is undefined” posture and makes re-evaluation deterministic.

## Scope / Constraints

```yaml
scope:
  policy_only: true
  docs_only: true
  runtime_changes: false
  submit_allowed: false
  automation: false
  stage_e: blocked
  outputs_versioned: false
```

## Source Policy (Must Remain True)

- `docs/ops/hyperliquid-submit-alert-horizon-policy.md` (#802)
- `docs/ops/hyperliquid-submit-session-evidence-contract.md`
- `docs/ops/d3-micro-runtime-supervision-slice.md`

## Window Selection (For #800)

```yaml
hyperliquid_submit_alert_window_for_800:
  mode: by_sessions
  value: 1
  reason:
    - "The operational risk comes from the latest attempt."
    - "Avoids artificial waiting by days."
    - "Forces the latest operational posture to be clean before GO."
```

Interpretation:
- The “current window” for #800 is defined as the latest 1 alert-bearing session by `activity_at`.
- Historical alerts remain preserved and visible, but do not block forever by themselves.

## GO Re-evaluation Criteria

```yaml
go_requires:
  current_window_alert_status: ok
  hard_freeze_present: false
  latest_session:
    terminal_state: known
    identifiers: present_if_submitted
    reconciliation: not_required
    exposure: closed_or_none
```

## Re-evaluation Triggers

```yaml
reevaluate_800_when:
  - "A newer session exists and is clean under window=1."
  - "OR there is an explicit operator memo that the latest critical no longer represents current operational state."
```

## Non-Submit Clarification (Important)

Creating a “clean newer session” does not require a new submit.

If tooling allows, the first evidence step may be:

- readiness / plan-only / signed-action drill evidence showing the `invalid_size` mitigation is in place

This memo does not authorize any submit to create a “clean latest” by force.

## Hard-Freeze Override (Always Blocks)

Even if the latest critical becomes historical under window selection, the following always block go/no-go:

```yaml
hard_freeze_even_if_historical:
  - reconciliation_ambiguity
  - missing_identifiers
  - unresolved_open_exposure
  - artifact_corruption
  - unknown_terminal_state
```

## Relationship to #800

Until this window selection is merged and applied, Issue #800 remains blocked:

```yaml
issue_800:
  status: open
  decision: NO_GO
  blocked_by:
    - "#804 window not merged/applied"
```

## Non-Goals

- This memo does not authorize submit.
- This memo does not change runtime behavior.
- This memo does not open Stage E.
