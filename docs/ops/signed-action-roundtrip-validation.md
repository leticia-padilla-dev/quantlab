# Signed Action Roundtrip Validation

Issue: [#835](https://github.com/leticia-padilla-dev/quantlab/issues/835)

Status: documentation-only validation record. No broker submit, live capital,
new signed artifact generation, Stage E activation, runtime change, or Stepbit
work was performed.

## Objective

Review the signed-action integrity prerequisite identified by:

- `docs/ops/stage-e-broker-live-scoping-prerequisites.md`
- `docs/ops/stage-e-broker-live-prerequisite-gap-review.md`
- `docs/ops/broker-no-submit-evidence-review.md`

The purpose is to determine whether the #800/#812 signed-action failure class
has a sufficient no-submit validation record for the Stage E prerequisite gate.

## Boundary

```yaml
boundary:
  docs_only: true
  broker_submit: false
  live_capital: false
  signed_action_generation: false
  stage_e_activation: false
  runtime_changes: false
  stepbit: false
```

This review inspected existing code, tests, documentation, and local evidence
only. It did not create a new signed action and did not contact a venue.

## Sources Reviewed

```yaml
sources:
  incident:
    - docs/ops/d3-issue-800-supervised-tiny-submit-rejection-freeze.md
    - docs/ops/d3-issue-812-rejected-submit-postmortem.md
  prerequisite_reviews:
    - docs/ops/stage-e-broker-live-scoping-prerequisites.md
    - docs/ops/stage-e-broker-live-prerequisite-gap-review.md
    - docs/ops/broker-no-submit-evidence-review.md
  implementation:
    - src/quantlab/brokers/hyperliquid.py
  tests:
    - test/test_hyperliquid_broker_adapter.py
  merged_fix:
    - "#810"
    - "commit 3f84aa7 fix(hyperliquid): canonicalize action hash for signed action artifacts"
```

## Incident Recap

The #800 supervised tiny submit produced a rejected terminal session:

```yaml
incident:
  issue: 800
  diagnostic_issue: 812
  session_id: 20260514_172736_hyperliquid_submit_70d57e2
  submit_state: submit_rejected
  exchange_response: "User or API Wallet 0x72a9c1ff16d274f68315d05ad88869e0b792daa8 does not exist."
  local_declared_signer: "0xeFed99a413a2Af80622f5b7566e011904d9a85B8"
  classified_failure_class: signed_action_artifact_round_trip_hash_mismatch
  retry_performed: false
  close_performed: false
  stage_e: blocked
```

#812 concluded that the important diagnostic signal was the mismatch between
the local declared signer and the wallet referenced by the exchange error. The
failure class was classified as a signed-action artifact round-trip/hash
mismatch class, not as a strategy, size, retry, or operator-discretion problem.

## #810 Fix Reviewed

#810 is represented locally by:

```yaml
fix:
  commit: 3f84aa7
  title: "fix(hyperliquid): canonicalize action hash for signed action artifacts"
  files_changed:
    - src/quantlab/brokers/hyperliquid.py
    - test/test_hyperliquid_broker_adapter.py
```

Relevant implementation properties:

```yaml
implementation:
  canonical_payload_function: _canonicalize_hyperliquid_action_payload
  behavior:
    - "dict keys are sorted by string key"
    - "nested dicts and lists are canonicalized recursively"
    - "action hash is computed from the canonicalized payload"
    - "msgpack.packb(..., use_bin_type=True) is used for hash input"
  relevant_paths:
    - "src/quantlab/brokers/hyperliquid.py:_canonicalize_hyperliquid_action_payload"
    - "src/quantlab/brokers/hyperliquid.py:_hyperliquid_action_hash"
    - "src/quantlab/brokers/hyperliquid.py:recover_hyperliquid_l1_action_signer"
```

The implementation now canonicalizes the action payload before hashing. This
is the correct local invariant for JSON artifact stability: if an action
payload is persisted and later reloaded as JSON, signer recovery should still
derive from the same canonical action hash.

## Test Coverage Reviewed

The relevant regression coverage is in:

```yaml
test:
  file: test/test_hyperliquid_broker_adapter.py
  test_name: test_hyperliquid_signed_action_report_signs_with_local_private_key
```

The test verifies the important invariants:

```yaml
covered_invariants:
  initial_signed_report:
    - readiness_allowed_is_true
    - signature_state_is_signed
    - signature_present_is_true
    - action_hash_is_present
    - derived_signer_address_is_present
    - identity_readiness_matches_derived_signer
    - signing_readiness_action_hash_matches_signature_envelope
    - connection_id_matches_action_hash

  direct_recovery:
    - recover_hyperliquid_l1_action_signer(...) matches derived_signer_address
    - recovered signer matches expected context.signer_id

  json_roundtrip_recovery:
    - report is serialized with json.dumps
    - report is reloaded with json.loads
    - recover_hyperliquid_l1_action_signer(...) still matches derived_signer_address
    - reloaded recovered signer still matches expected context.signer_id
```

This directly targets the failure class from #800/#812: a signed-action report
must remain signer-stable after JSON artifact round-trip.

## What This Validates

```yaml
validated:
  - "#800 failure class is documented and understood."
  - "#810 changed the local hash/signature path relevant to that failure class."
  - "Action payload hashing now canonicalizes nested payloads before msgpack hashing."
  - "The regression test asserts signer recovery before JSON persistence."
  - "The regression test asserts signer recovery after JSON dump/load round-trip."
  - "The regression test asserts recovered signer equals the expected signer id."
```

## What This Does Not Validate

```yaml
not_validated:
  - "No new signed action was generated by this review."
  - "No broker submit was attempted."
  - "No exchange-side signer recovery was observed."
  - "No Stage E dry run was performed."
  - "No live capital or broker readiness is implied."
  - "No claim is made that every future venue error is eliminated."
```

The exchange-internal signer recovery details from #800 remain not locally
provable. The local invariant that can be proven is that QuantLab's persisted
signed-action artifact remains signer-stable across JSON round-trip.

## Decision

```yaml
decision:
  signed_action_integrity:
    status: satisfied
    scope: static_no_submit_stage_e_prerequisite_review
    reason:
      - "#812 classified the failure class."
      - "#810 canonicalized action hashing and submit payload construction."
      - "Regression coverage verifies signer recovery before and after JSON round-trip."
      - "No-submit review confirms the local invariant required by the prerequisite gate."

  broker_readiness:
    status: not_ready
    reason:
      - "Reconciliation evidence pack remains pending."
      - "Stop-control dry drill remains pending."
      - "Artifact durability review remains pending."
      - "Stage E is still not scopeable until the remaining gaps are closed."

  stage_e:
    remains_blocked: true
```

## Remaining Gaps

This issue closes only the signed-action roundtrip prerequisite record. The
remaining Stage E prerequisite gaps are unchanged:

```yaml
remaining_gaps:
  reconciliation_evidence_pack:
    title: "ops(broker): build reconciliation evidence pack for Stage E prerequisites"

  stop_control_dry_drill:
    title: "ops(broker): run stop-control dry drill against existing artifacts"

  artifact_durability_review:
    title: "ops(stage-e): verify broker evidence artifact durability"
```

## Final Boundary

Do not use this document to authorize Stage E, broker submit, live capital,
signed action generation, runtime changes, Stepbit work, retry of #800, or any
exchange interaction.
