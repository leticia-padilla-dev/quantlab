# Hyperliquid: Submit Session Evidence Contract

Issue: #796

Status: docs-only. No runtime changes. No submit expansion. Stage E remains blocked.

## Purpose

After QuantLab can deterministically prepare and sign actions, the remaining risk surface becomes operational:

- what artifacts must exist after a supervised submit
- when a session is terminal
- when reconciliation is required
- when it is forbidden to open a new session

This contract defines a minimum, deterministic evidence standard for Hyperliquid submit sessions without redefining the runbook.

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Source of Truth (Referenced, Not Rewritten)

- [supervised-broker-runbook.md](../supervised-broker-runbook.md)
- [d3-reconciliation-walkthrough.md](./d3-reconciliation-walkthrough.md)
- [stage-e-evidence-index.md](./stage-e-evidence-index.md)
- [d3-operator-hardening-declarations.md](./d3-operator-hardening-declarations.md)

## Canonical Hyperliquid Submit Session Root

```text
outputs/hyperliquid_submits/<session_id>/
```

## Required Artifacts (Minimum)

These artifacts are required to claim a Hyperliquid submit session is interpretable as evidence:

```yaml
required_minimum:
  - session_metadata.json
  - session_status.json
  - hyperliquid_signed_action.json
  - hyperliquid_submit_response.json
```

Meaning:
- `session_metadata.json` anchors identity, timestamps, reviewer lineage, and request linkage.
- `session_status.json` is the authoritative lifecycle summary (terminality, state, error codes).
- `hyperliquid_signed_action.json` anchors what was signed (intent, quantization, signer identity, signature envelope).
- `hyperliquid_submit_response.json` anchors what was sent/attempted remotely and the remote response snapshot.

## Conditional Artifacts (Flow-Dependent)

These artifacts are required only when the session claims a specific action occurred.

```yaml
conditional_required:
  status_refresh_claimed:
    - hyperliquid_order_status.json
  reconciliation_claimed_or_required:
    - hyperliquid_reconciliation.json
  fills_claimed:
    - hyperliquid_fill_summary.json
  supervision_claimed:
    - hyperliquid_supervision.json
  cancel_claimed:
    - hyperliquid_cancel_response.json
```

## Completeness Levels

```yaml
completeness_levels:
  A_minimum_interpretable:
    description: "All required_minimum artifacts exist and parse."
    allowed_actions:
      - continue_evidence_capture
    forbidden_actions:
      - infer_missing_fields_from_console_logs
      - open_new_session_if_any_freeze_condition_applies

  B_reconciliation_ready:
    description: "A_minimum_interpretable + hyperliquid_reconciliation.json exists and resolves identity deterministically."
    allowed_actions:
      - classify_terminality
      - proceed_with_supervised_stop_control_only_if_reconciliation_proves_exposure

  C_terminal_evidence_pack:
    description: "B_reconciliation_ready + terminality is proven + any claimed fill/close artifacts exist."
    allowed_actions:
      - archive_as_completed_evidence

  D_incomplete:
    description: "Any required_minimum artifact missing or not parseable."
    allowed_actions:
      - stop
      - escalate

  E_ambiguous:
    description: "Artifacts exist but session identity, remote identifiers, or reconciliation outcomes are ambiguous."
    allowed_actions:
      - stop
      - reconcile
```

## Severity Mapping (Deterministic)

```yaml
severity_mapping:
  - condition: "session_status.json missing OR not parseable"
    severity: critical
    action: stop

  - condition: "session_metadata.json missing OR not parseable"
    severity: critical
    action: stop

  - condition: "hyperliquid_signed_action.json missing OR not parseable"
    severity: critical
    action: stop

  - condition: "hyperliquid_submit_response.json missing OR not parseable"
    severity: critical
    action: stop

  - condition: "submit_response indicates remote_submit_called == true AND hyperliquid_reconciliation.json missing"
    severity: critical
    action: stop_and_reconcile

  - condition: "reconciliation indicates reconciliation_required OR unknown OR identifiers_missing"
    severity: critical
    action: stop_and_reconcile

  - condition: "session claims cancel occurred AND hyperliquid_cancel_response.json missing"
    severity: critical
    action: stop

  - condition: "session claims fills are known AND hyperliquid_fill_summary.json missing"
    severity: critical
    action: stop

  - condition: "session claims status refresh occurred AND hyperliquid_order_status.json missing"
    severity: warning
    action: stop
```

## Freeze Conditions (Hard Stop)

Freeze means: do not open a new submit session until the condition is resolved deterministically.

```yaml
freeze_conditions:
  - "any required_minimum artifact missing"
  - "reconciliation_required or ambiguous reconciliation outcome"
  - "remote identifiers missing after submit (e.g. missing oid/cloid)"
  - "conflicting artifacts (e.g. status says filled but fills artifact absent)"
  - "operator cannot explain current exposure deterministically from artifacts"
```

## No-New-Session Conditions

These conditions are stricter than “stop”: they forbid creating another session because doing so increases ambiguity.

```yaml
no_new_session_conditions:
  - "any freeze_conditions apply"
  - "an existing session under outputs/hyperliquid_submits is in reconciliation_required posture"
  - "health/alerts indicate critical state tied to missing identifiers or ambiguous reconciliation"
  - "operator is not present (supervision required)"
```

## Operator Checklist (Copy/Paste)

```yaml
hyperliquid_submit_evidence_review:
  session_id: "<hyperliquid_submit_session_id>"
  required_minimum:
    session_metadata_json: false
    session_status_json: false
    hyperliquid_signed_action_json: false
    hyperliquid_submit_response_json: false
  conditional:
    hyperliquid_reconciliation_json: false
    hyperliquid_order_status_json: false
    hyperliquid_fill_summary_json: false
    hyperliquid_cancel_response_json: false
    hyperliquid_supervision_json: false
  completeness_level: A_minimum_interpretable
  severity: ok | warning | critical
  freeze: false
  next_action: stop | reconcile | continue_evidence_capture
```

## Non-Goals

- This contract does not authorize new submit work.
- This contract does not define or expand automation.
- This contract does not open Stage E.
