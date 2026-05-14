# D.3 Issue #800 — GO Candidate Gate (Authorization Readiness, Not Execution Permission)

Refs: [#800](https://github.com/Whiteks1/quantlab/issues/800)

This gate defines authorization readiness boundaries, not execution permission.

Status: docs-only operational gate. No runtime changes. No submit authorized. Stage E remains blocked.

## Purpose

Convert Issue #800 from:

- `pending_GO_review`

to:

- `GO_candidate_ready_for_single_supervised_entry_approval`

This gate does not authorize submit or any execution.

## Scope / Constraints

```yaml
scope:
  docs_only: true
  runtime_changes: false
  submit_authorized: false
  stage_e: blocked
```

## Inputs / References

- `docs/ops/d3-issue-800-go-reevaluation-window.md` (window: `by_sessions: 1`)
- `docs/ops/d3-issue-800-plan-only-go-reevaluation.md` (plan-only evidence; no submit)
- `docs/ops/hyperliquid-submit-alert-horizon-policy.md`
- `docs/ops/d3-micro-runtime-supervision-slice.md`
- `docs/ops/hyperliquid-submit-session-evidence-contract.md`
- `docs/ops/d3-reconciliation-walkthrough.md`
- `docs/ops/d3-operator-hardening-declarations.md`

## Gate Checklist (Pre-Authorization)

```yaml
gate_checklist:
  operator_present: true

  operator_understands_boundary:
    stage_e_blocked: true
    signed_action_not_submit_authority: true

  plan_only_evidence_verified:
    signature_state: signed
    readiness_allowed: true
    readiness_reasons: []
    size_diagnostic_state: ok
    submit_performed: false

  submit_sessions_posture_checked:
    performed: true
    window_mode: by_sessions
    window_value: 1
    hard_freeze_present: false

  no_retry_widening:
    allowed: false

  explicit_override_if_latest_submit_is_critical:
    required_if_current_window_alert_status_is_not_ok: true
    operator_declares:
      - "latest critical (invalid_size) is considered mitigated by signed plan-only evidence"
      - "next step, if approved, is exactly one supervised tiny entry attempt"
      - "no retry widening; stop+freeze on any ambiguity"
      - "this is NOT Stage E and does not authorize ongoing execution"
```

Notes:
- `hard_freeze_present` and `current_window_alert_status` must be derived by applying the horizon policy over `outputs/hyperliquid_submits/*` using `window_value: 1`.
- If `hard_freeze_present: true`, this gate fails regardless of window interpretation.

## Stop / Freeze Rules (Always Apply)

```yaml
stop_if:
  - plan_only evidence missing
  - signature_state != signed
  - readiness_allowed != true
  - readiness_reasons != []
  - size_diagnostic_state != ok
  - hard_freeze_present == true
  - reconciliation_required session exists
  - identifiers missing (for any submitted session)
  - operator cannot explain exposure from artifacts
```

## Decision Output

```yaml
decision:
  issue_800: GO_candidate_ready_for_single_supervised_entry_approval
  submit_authorized: false
  stage_e: blocked
```

## Non-Goals

- This gate does not authorize submit.
- This gate does not approve execution.
- This gate does not transition Stage E.
