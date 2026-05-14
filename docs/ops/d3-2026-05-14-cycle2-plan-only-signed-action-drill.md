# D.3 2026-05-14 — Cycle 2 Plan-Only Signed Action Drill (Evidence Memo)

Issue: [#792](https://github.com/Whiteks1/quantlab/issues/792)

artifact_type: operational_evidence_memo

## Scope / Constraints

```yaml
scope:
  d3_cycle2: true
  mode:
    - supervised
    - plan_only
    - non_executing
  submit_allowed: false
  broker_execution: false
  automation: false
  stage_e: blocked
  docs_only: true
  outputs_versioned: false
```

## Purpose

Freeze auditable evidence that the D.3 cycle2 operator workflow is deterministic for:

- preflight (price + size_decimals)
- account readiness (identity + signing surface)
- quantization (floor, based on preflight size_decimals)
- signed action generation (envelope only)
- stop conditions (explicit, hard stop)
- authority boundary (signed action is not submit authority)

## Local Evidence (Not Versioned)

The drill outputs are local operational artifacts. They must not be committed.

```yaml
local_outputs:
  root_dir: outputs/d3_repeatability_cycle2_<timestamp>
  expected_files:
    - outputs/d3_repeatability_cycle2_<timestamp>/preflight/broker_preflight.json
    - outputs/d3_repeatability_cycle2_<timestamp>/account_readiness/hyperliquid_account_readiness.json
    - outputs/d3_repeatability_cycle2_<timestamp>/entry_signed_action/hyperliquid_signed_action.json
```

## Failure Context: `invalid_size`

This drill exists to re-test and mitigate the previously observed failure mode:

```yaml
previous_failure:
  code: invalid_size
  mitigation:
    source_of_truth: preflight.size_decimals
    strategy: floor_quantization
```

## Deterministic Quantization Record

```yaml
quantization:
  inputs:
    notional_usd: 500
    preflight_mid_price: "2261.75"
    preflight_size_decimals: 4
  computation:
    raw_qty: "0.2210677572676025201724328507"
    quantization_strategy: floor
    quantized_qty: "0.221"
```

## Signed Action Readiness Snapshot (From Artifact)

Populate these fields from the generated `hyperliquid_signed_action.json` (local file).

```yaml
signed_action_snapshot:
  generated_at: "2026-05-14T16:18:57"
  signer_backend: null
  signature_state: pending_signer_backend
  signature_reason: signature_backend_not_implemented
  readiness_allowed: false
  readiness_reasons:
    - missing_account_id
    - missing_execution_account_id
    - missing_signer_id
    - missing_nonce_scope
  size_diagnostic:
    diagnostic_state: ok
    size_decimals: 4
    size_step: "0.0001"
    formatted_size: "0.221"
    decimal_places: 3
    precision_ok: true
    multiple_ok: true
    suggested_floor_size: "0.221"
```

## Stop Conditions (Hard Stop)

```yaml
stop_conditions:
  ready_eval:
    ready_if:
      - signature_state == signed
      - readiness_reasons == []
  if_not_ready:
    - stop
    - do_not_submit
    - exit_code: 2
```

## Authority Boundary Banner (Runtime Output)

The drill must print this banner regardless of readiness to freeze operator semantics:

```text
NO SUBMIT AUTHORIZED
STAGE_E_BLOCKED
signed_action != submit_authority
```

## Operator Declaration (Manual Signature Required)

This memo must not be considered complete without an operator signature.

```yaml
operator_declaration:
  understands:
    - "historical vs current window posture is a separate surface (paper); it does not grant submit authority"
    - "signed action generation is an envelope/signing surface test, not execution permission"
    - "invalid_size mitigation is preflight.size_decimals + floor quantization"
  decision:
    next_action: stop
    rationale: "readiness_allowed=false; readiness_reasons=[missing_account_id, missing_execution_account_id, missing_signer_id, missing_nonce_scope]; signature_state=pending_signer_backend (signature_backend_not_implemented)."
  operator_signature:
    signed_by: Leti
    signed_at: "2026-05-14T16:19:49+02:00"
    status: signed_by_operator
```
