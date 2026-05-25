# D.3 Issue #812 - #800 Rejected Submit Post-Mortem

Refs:

- [#800](https://github.com/leticia-padilla-dev/quantlab/issues/800)
- [#812](https://github.com/leticia-padilla-dev/quantlab/issues/812)
- [#810](https://github.com/leticia-padilla-dev/quantlab/pull/810)

Status: docs-only post-mortem. No broker action performed.

## Executive Summary

```yaml
postmortem:
  subject_issue: 800
  diagnostic_issue: 812
  session_id: 20260514_172736_hyperliquid_submit_70d57e2
  outcome: submit_rejected
  exchange_response: "User or API Wallet 0x72a9c1ff16d274f68315d05ad88869e0b792daa8 does not exist."
  local_declared_signer: "0xeFed99a413a2Af80622f5b7566e011904d9a85B8"
  likely_failure_class: "signed action payload/hash mismatch after artifact round-trip"
  supporting_fix: "#810 canonicalized Hyperliquid action hashing and submit payload construction"
  confidence: high
  freeze_active: true
  submit_performed_in_this_diagnostic: false
  retry_performed: false
  close_performed: false
  stage_e: blocked
```

The #800 supervised tiny submit was rejected by Hyperliquid. Local artifacts show
the signed action declared signer/account `0xeFed99a413a2Af80622f5b7566e011904d9a85B8`,
but the exchange error identified recovered user/API wallet
`0x72a9c1ff16d274f68315d05ad88869e0b792daa8`.

That mismatch is the important diagnostic signal. It is more consistent with a
signature/action-hash mismatch than with an order-size, price, readiness, or
policy rejection.

## Boundary

```yaml
diagnostic_boundary:
  docs_only: true
  broker_submit: false
  retry: false
  close: false
  signed_action_generation: false
  runtime_changes: false
  desktop_changes: false
  stepbit: false
  stage_e: blocked
```

This memo inspected existing artifacts only.

## Artifact Inventory

Rejected #800 session:

```text
outputs/hyperliquid_submits/20260514_172736_hyperliquid_submit_70d57e2/
```

Available artifacts:

```yaml
rejected_session_artifacts:
  - hyperliquid_order_status.json
  - hyperliquid_signed_action.json
  - hyperliquid_submit_response.json
  - session_metadata.json
  - session_status.json
```

Missing artifacts:

```yaml
missing_expected_after_rejected_submit:
  - hyperliquid_reconciliation.json
  - hyperliquid_fill_summary.json
```

Interpretation:

- Missing reconciliation/fill artifacts are expected for a rejected submit with
  no `oid` or `cloid`.
- `hyperliquid_order_status.json` records `missing_order_identifier` and
  `query_attempted: false`, which is consistent with no remote order identifier.

Comparison sessions:

```yaml
successful_d3_entry:
  session_id: 20260502_230137_hyperliquid_submit_7209d49
  submit_state: submitted_remote
  order_status_state: filled
  reconciliation_state: filled
  close_state: closed

successful_d3_reduce_only_close:
  session_id: 20260502_232513_hyperliquid_submit_5d599f8
  submit_state: submitted_remote
  order_status_state: filled
  reconciliation_state: filled
  close_state: closed
```

## Observed Facts

### Rejected session

```yaml
session:
  session_id: 20260514_172736_hyperliquid_submit_70d57e2
  submit_state: submit_rejected
  submitted: false
  remote_submit_called: true
  response_type: err
  errors:
    - exchange_status:err
  source_signer_id: "0xeFed99a413a2Af80622f5b7566e011904d9a85B8"
  source_action_hash: "36a8b4d06fb76d9b94f495426006ad965d0e9693fa1b1f0d169c7392e89a3ef1"
  source_signing_payload_sha256: "2e1b4045dd04c225e99db7a8b5ba734671807391bb1528927357de4e2354ddc3"
  exchange_response:
    status: err
    response: "User or API Wallet 0x72a9c1ff16d274f68315d05ad88869e0b792daa8 does not exist."
```

### Signed action readiness

The signed action artifact for #800 reported:

```yaml
signed_action_readiness:
  identity_ready: true
  declared_execution_account_id: "0xeFed99a413a2Af80622f5b7566e011904d9a85B8"
  declared_execution_signer_id: "0xeFed99a413a2Af80622f5b7566e011904d9a85B8"
  derived_signer_address: "0xeFed99a413a2Af80622f5b7566e011904d9a85B8"
  readiness_allowed: true
  readiness_reasons: []
  signing_ready: true
  signing_reasons: []
```

### Submitted action payload

The submitted order payload was:

```yaml
submit_action:
  type: order
  grouping: na
  orders:
    - a: 1
      b: true
      p: "2300.0"
      r: false
      s: "0.0065"
      t:
        limit:
          tif: Ioc
```

The payload shape is structurally comparable to earlier accepted D.3 entry and
close sessions, which used the same account, same direct signer type, same
coin id, and IOC limit order structure.

## What Can Be Proven

```yaml
proven:
  - "Exactly one submit attempt occurred for #800."
  - "The exchange rejected the submit before an oid/cloid was produced."
  - "No retry occurred."
  - "No close was required because no open exposure was proven from this session."
  - "The exchange error referenced wallet 0x72a9..., not the locally declared signer/account 0xeFed...."
  - "The local artifact declared identity/signing readiness as clean before submit."
  - "#810 later changed Hyperliquid action hashing and submit payload construction to canonicalize action payloads."
```

## What Cannot Be Proven From Existing Artifacts

```yaml
not_proven:
  - "The exact recovered signer derivation performed by Hyperliquid internally."
  - "Whether Hyperliquid's error string exposes the recovered signer, API wallet, or another internal wallet classification."
  - "A remote order lifecycle, because no oid/cloid was returned."
  - "A fill, because no order identifier or fill artifact exists."
```

This means the post-mortem can classify the failure class with high confidence,
but it should not claim a fully proven exchange-internal root cause.

## Hypothesis Review

### H1 - Size or min-value rejection

Assessment: unlikely as primary cause.

Evidence:

- #800 had prior plan-only evidence with `size_diagnostic_state: ok`.
- The exchange error did not report invalid size or min value for the #800
  terminal submit.
- The rejected response was an identity/wallet error, not an order-constraint
  error.

### H2 - Account readiness failure before submit

Assessment: unlikely as primary cause.

Evidence:

- Signed action artifact reported `identity_ready: true`.
- Signed action artifact reported `readiness_allowed: true`.
- Account readiness reported the direct signer/account as visible and matched.

### H3 - Missing order identifier after accepted submit

Assessment: not the root cause.

Evidence:

- `oid` and `cloid` were missing because the exchange returned `status: err`.
- `hyperliquid_order_status.json` correctly did not query remote status and
  recorded `missing_order_identifier`.

### H4 - Signed action payload/hash mismatch after artifact round-trip

Assessment: likely root cause class.

Evidence:

- Local artifact declared signer/account `0xeFed...`.
- Exchange error referenced `0x72a9...`.
- This mismatch is consistent with the exchange recovering a different signer
  from the submitted action/signature pair.
- The follow-up fix #810 changed the Hyperliquid adapter to canonicalize action
  payloads before hashing and before building submit payloads.
- #810 also added a regression assertion that a JSON-reloaded signed action can
  still recover the original signer.

Conclusion:

```yaml
likely_root_cause_class: "pre-#810 signed action artifact was not stable across JSON artifact round-trip into submit payload"
operational_interpretation: "do not treat #800 rejection as strategy, size, or operator retry problem"
```

## Relationship To #810

#810 changed the Hyperliquid adapter in the relevant area:

```yaml
fix_810:
  title: "fix(hyperliquid): canonicalize action hash for signed action artifacts"
  relevant_changes:
    - "canonicalize action payload before effective signed action use"
    - "canonicalize action payload before submit payload construction"
    - "use msgpack.packb(..., use_bin_type=True) over canonical payload"
    - "add JSON round-trip signer recovery regression coverage"
```

This directly addresses the failure class observed in #800: signed artifacts
must remain valid when persisted as JSON and later consumed for submit.

## Freeze Status

```yaml
freeze:
  active: true
  reason:
    - "#800 terminal submit_rejected"
    - "D.3 cycle ended as NO_GO"
    - "post-mortem diagnostic only"
  forbidden:
    - retry
    - second submit
    - close
    - Stage E
    - automation
```

The freeze remains active for #800. #810 may remove the specific artifact
round-trip bug class for future validation, but it does not retroactively
authorize a new submit.

## Allowed Next Work

```yaml
allowed_next_work:
  - "review this memo"
  - "review #810 test coverage"
  - "run no-submit unit tests around signed action artifact round-trip"
  - "open a separate pre-submit validation issue if more static checks are needed"
```

## Forbidden Next Work From This Memo

```yaml
forbidden_next_work:
  - "no broker submit"
  - "no retry"
  - "no close"
  - "no signed action generation for live submit"
  - "no Stage E"
  - "no Desktop submit authority"
  - "no Stepbit execution path"
```

## Diagnostic Verdict

```yaml
diagnostic_verdict:
  status: classified
  confidence: high
  root_cause_class: signed_action_artifact_round_trip_hash_mismatch
  specific_runtime_fix_already_merged: "#810"
  remaining_diagnostic_gap: "exchange-internal signer recovery details cannot be proven locally"
  issue_812_closure_recommendation: "manual review before close"
```

Recommendation: keep #812 referenced, not automatically closed by this PR,
unless the reviewer agrees that #810 and this memo are sufficient to close the
diagnostic loop.
