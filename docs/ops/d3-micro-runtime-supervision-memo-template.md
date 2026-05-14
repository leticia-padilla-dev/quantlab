# D.3 Micro-Runtime Supervision Memo (Template)

Issue: #798

artifact_type: operational_evidence_memo

## Scope / Constraints

```yaml
scope:
  d3_micro_runtime: true
  docs_only_template: true
  supervised: true
  submit_allowed: false
  broker_execution: false
  automation: false
  stage_e: blocked
  outputs_versioned: false
```

## Purpose

Freeze auditable operational evidence for the first D.3 micro-runtime workflow:

- entry submit (tiny) under supervision
- mandatory reconciliation
- conditional reduce-only close
- freeze and no-new-session enforcement

## Local Evidence (Not Versioned)

```yaml
local_outputs:
  root_dir: outputs/hyperliquid_submits
  entry_session_dir: outputs/hyperliquid_submits/<entry_session_id>
  close_session_dir: outputs/hyperliquid_submits/<close_session_id_or_null>
```

## Entry Session Summary (Populate From Artifacts)

```yaml
entry_session:
  session_id: <fill>
  session_dir: outputs/hyperliquid_submits/<fill>
  artifact_pack_review:
    required_minimum:
      session_metadata_json: <fill true|false>
      session_status_json: <fill true|false>
      hyperliquid_signed_action_json: <fill true|false>
      hyperliquid_submit_response_json: <fill true|false>
    conditional:
      hyperliquid_reconciliation_json: <fill true|false>
      hyperliquid_order_status_json: <fill true|false>
      hyperliquid_fill_summary_json: <fill true|false>
      hyperliquid_cancel_response_json: <fill true|false>
      hyperliquid_supervision_json: <fill true|false>
    completeness_level: <fill>
    severity: <fill ok|warning|critical>
    freeze: <fill true|false>
  signed_action_snapshot:
    signature_state: <fill>
    readiness_reasons: <fill>
    size_decimals: <fill>
    intent_quantity: <fill>
  submit_snapshot:
    submit_state: <fill>
    remote_submit_called: <fill true|false>
    identifiers_present: <fill true|false>
  reconciliation_result:
    state: <fill>
    terminal: <fill true|false>
    exposure_proven: <fill true|false>
    close_required: <fill true|false>
```

## Close Session (Reduce-Only) Summary (Conditional)

If `close_required` is true and reconciliation proves exposure exists, populate this block. Otherwise set `performed: false`.

```yaml
close_session:
  performed: <fill true|false>
  session_id: <fill or null>
  session_dir: outputs/hyperliquid_submits/<fill or null>
  constraints_acknowledged:
    reduce_only: true
    one_session_only: true
    reconciliation_mandatory: true
  artifact_pack_review:
    required_minimum:
      session_metadata_json: <fill true|false>
      session_status_json: <fill true|false>
      hyperliquid_signed_action_json: <fill true|false>
      hyperliquid_submit_response_json: <fill true|false>
    conditional:
      hyperliquid_reconciliation_json: <fill true|false>
      hyperliquid_order_status_json: <fill true|false>
      hyperliquid_fill_summary_json: <fill true|false>
      hyperliquid_cancel_response_json: <fill true|false>
      hyperliquid_supervision_json: <fill true|false>
    completeness_level: <fill>
    severity: <fill ok|warning|critical>
    freeze: <fill true|false>
  reconciliation_result:
    state: <fill>
    terminal: <fill true|false>
    exposure_closed_proven: <fill true|false>
```

## Freeze / No-New-Session Declaration

```yaml
freeze_policy_application:
  freeze_active: <fill true|false>
  no_new_session_enforced: <fill true|false>
  reasons:
    - <fill>
```

## Authority Boundary Banner (Must Remain True)

```text
NO SUBMIT AUTHORIZED
STAGE_E_BLOCKED
signed_action != submit_authority
```

## Operator Declaration (Manual Signature Required)

```yaml
operator_declaration:
  understands:
    - "This memo does not authorize submit expansion or automation."
    - "If reconciliation is ambiguous, the correct action is stop and no new session."
    - "Reduce-only close is only allowed if reconciliation proves exposure exists and close is required."
  decision:
    next_action: stop | freeze | proceed_to_next_governed_step
    rationale: ""
  operator_signature:
    signed_by: <fill>
    signed_at: <fill>
    status: pending_operator_signature
```
