# D3 Supervised Micro-Live Evidence Cycle #749 — Entry Rejected (invalid_size) — 2026-05-14

## Scope

One supervised Hyperliquid micro-live attempt under Stage D.3 discipline.

stop_on_ambiguity: true
no_retry: true
second_submit_allowed: false
stage_e: blocked

This memo records what happened. It does not attempt to repair the outcome with a second submit.

## Input Parameters (planned)

symbol: ETH
entry_side: buy
entry_notional: 15
entry_quantity: 0.00661492
reduce_only: false
account_id_choice:
  source: outputs/d3_446/signed/hyperliquid_signed_action.json
  reason:
    - same operational boundary as prior D.3
    - maximum comparability
    - avoid implicit identity
    - avoid missing_account_id
    - reduce ambiguity before submit

## Evidence Artifacts

### Read-only preparation

- outputs/d3_749/preflight/broker_preflight.json
- outputs/d3_749/account_readiness/hyperliquid_account_readiness.json
- outputs/d3_749/entry_signed_action/hyperliquid_signed_action.json

### Canonical submit session (attempted)

entry_session: outputs/hyperliquid_submits/20260514_090121_hyperliquid_submit_8ae1921

Reviewed artifacts:

- session_metadata.json
- session_status.json
- hyperliquid_signed_action.json
- hyperliquid_submit_response.json
- hyperliquid_reconciliation.json
- hyperliquid_fill_summary.json

### Aggregates refreshed

- outputs/hyperliquid_submits/hyperliquid_submits_health.json
- outputs/hyperliquid_submits/hyperliquid_submits_alerts.json

## Observed Result

### Submit

submit_state: submit_rejected
remote_submit_called: true
submitted: false
rejection_reason: invalid_size
rejection_message: "Order has invalid size."

The submit response preserved the exchange status error under:

- outputs/hyperliquid_submits/20260514_090121_hyperliquid_submit_8ae1921/hyperliquid_submit_response.json

### Signature state at submit time

The signed action persisted inside the submit session was submit-ready:

- signature_state: signed
- signature_present: true
- private_key_source: env:HYPERLIQUID_PRIVATE_KEY

## Reconciliation / Fills

fill_count: 0
fills_known: false
status_known: false
close_required: false

Reconciliation outcome is consistent with a rejected submit that returned no order identifiers:

- missing_order_identifier
- oid: null
- cloid: null

No position was opened. No reduce-only close is authorized.

## Health / Alerts

alert_status: critical
alert_code: HYPERLIQUID_SUBMIT_REJECTED
alert_message: "status_error:Order has invalid size."

## Classification

classification:
  cycle_result: entry_rejected
  rejection_reason: invalid_size
  close_required: false
  repeatability_cycle_completed: false
  no_retry_policy_followed: true
  stage_e: blocked

## Evidence Value

evidence_value:
  - signed action submit-ready
  - remote submit attempted
  - rejection preserved as artifact
  - reconciliation attempted
  - no fill
  - no close needed
  - health/alerts refreshed
  - operator stopped (no retry)

## Decision

This attempt is valid D.3 evidence for operational discipline and artifact preservation, but it does not satisfy the original goal of a complete entry + reduce-only close repeatability cycle.

Close #749 as completed_with_rejected_submit_evidence (not as a completed repeatability cycle).
