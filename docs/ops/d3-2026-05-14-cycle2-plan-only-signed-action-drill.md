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
    notional_usd: <fill>
    preflight_mid_price: <fill>
    preflight_size_decimals: <fill>
  computation:
    raw_qty: <fill>
    quantization_strategy: floor
    quantized_qty: <fill>
```

## Signed Action Readiness Snapshot (From Artifact)

Populate these fields from the generated `hyperliquid_signed_action.json` (local file).

```yaml
signed_action_snapshot:
  generated_at: <fill>
  signer_backend: <fill>
  signature_state: <fill>
  signature_reason: <fill or null>
  readiness_allowed: <fill>
  readiness_reasons: <fill>
  size_diagnostic: <fill>
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
    next_action: stop | proceed_plan_only
    rationale: ""
  operator_signature:
    signed_by: Leti
    signed_at: <fill>
    status: pending_operator_signature
```
