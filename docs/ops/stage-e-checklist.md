# Stage E Operational Checklist (Before Any Runtime Slice)

Issue: [#736](https://github.com/Whiteks1/quantlab/issues/736)

Date: 2026-05-13

Status: checklist-only. No runtime changes.

## Source of Truth

- `docs/ops/stage-e-scoping.md`
- `docs/d3-hardening-and-promotion-criteria.md`
- `docs/supervised-broker-runbook.md`
- `docs/ops/d3-operator-hardening-declarations.md` (issue #669)
- `docs/ops/supervised-paper-live-pack-reaudit-post-d3-drills.md` (issue #723)

## Current Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  docs_only_default: true
  runtime_open: false
```

## Checklist: Operator Knows

Complete only when the operator can answer each item without inspecting raw JSON.

- [ ] Current state: Stage E is scoped, bounded, and blocked.
- [ ] Stop rules: ambiguity means stop; no “second session” after unclear reconciliation.
- [ ] Reconciliation rule: `reconciliation_required` is a hard stop, not a reason to retry.
- [ ] Alert model: root-level aggregate can remain `critical` while latest-session is `ok`.
- [ ] Emergency paths: emergency UI close is last resort only when QuantLab artifacts are unavailable or ambiguous.
- [ ] Authority boundary: Desktop is not a submit authority; Stepbit is not a control surface.

## Checklist: Evidence Exists (Canonical Artifacts)

The operator can locate the evidence with file paths, not memory.

- [ ] D.3 declaration record is present and complete:
  - `docs/ops/d3-operator-hardening-declarations.md`
  - `operator_declarations_complete: true`
- [ ] D.3 hardening criteria document is present:
  - `docs/d3-hardening-and-promotion-criteria.md`
- [ ] Stage E scoping boundary document is present:
  - `docs/ops/stage-e-scoping.md`
- [ ] Re-audit confirms scoping eligibility while Stage E remains blocked:
  - `docs/ops/supervised-paper-live-pack-reaudit-post-d3-drills.md`
  - `stage_e: blocked`
  - `stage_e_scoping_issue_allowed: true`

## Checklist: Evidence Exists (Operational Session Anchors)

These are the minimum anchor paths required for operator navigation and ambiguity handling drills.

```yaml
required_session_paths:
  hyperliquid_entry_session:
    path: outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49
    required_artifacts:
      - session_status.json
      - hyperliquid_submit_response.json
      - hyperliquid_order_status.json
      - hyperliquid_reconciliation.json
  hyperliquid_reduce_only_close_session:
    path: outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8
    required_artifacts:
      - session_status.json
      - hyperliquid_submit_response.json
      - hyperliquid_order_status.json
      - hyperliquid_reconciliation.json
```

## Checklist: Ambiguity Policy (Non-Negotiable)

```yaml
ambiguity_policy:
  stop_immediately: true
  no_widening_retry: true
  no_automatic_ambiguity_resolution: true
  allow_emergency_ui_close_only_when:
    - "QuantLab artifacts are unavailable"
    - "QuantLab artifacts are ambiguous"
  after_emergency_ui_close:
    required:
      - "record evidence"
      - "run reconciliation"
      - "document final classification"
```

## Checklist: Runtime Slice Authorization Preconditions

Runtime work is not allowed until all items below are true.

- [ ] This checklist is complete and recorded as reviewed by the operator.
- [ ] An evidence navigation index exists (issue #737).
- [ ] Repeatability criteria exist (issue #738).
- [ ] Alert confidence matrix exists (issue #739).
- [ ] Runtime slice authorization policy exists (issue #740).
- [ ] A separate issue explicitly authorizes the first runtime slice (no implied permission).

## Completion Record (When All Boxes Are Checked)

```yaml
e0_checklist:
  status: complete_or_incomplete
  reviewed_by_operator: false
  review_date: null
  notes: null
```
