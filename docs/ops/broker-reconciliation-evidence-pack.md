# Broker Reconciliation Evidence Pack

Issue: [#837](https://github.com/leticia-padilla-dev/quantlab/issues/837)

Status: documentation-only static artifact review. No broker submit, live
capital, signed action generation, cancel, close, runtime change, Stepbit work,
or Stage E activation was performed.

## Objective

Build a focused reconciliation evidence pack for Stage E prerequisites using
existing local artifacts under:

```text
outputs/hyperliquid_submits
```

This closes the reconciliation evidence gap identified in:

- `docs/ops/stage-e-broker-live-scoping-prerequisites.md`
- `docs/ops/stage-e-broker-live-prerequisite-gap-review.md`
- `docs/ops/broker-no-submit-evidence-review.md`

## Boundary

```yaml
boundary:
  docs_only: true
  static_artifact_review: true
  broker_submit: false
  live_capital: false
  signed_action_generation: false
  cancel: false
  close: false
  runtime_changes: false
  stepbit: false
  stage_e_activation: false
```

This pack does not refresh, retry, reconcile remotely, or mutate any broker
state. It only maps existing evidence to operator-readable reconciliation
states.

## Sources Reviewed

```yaml
sources:
  reconciliation_guide:
    - docs/ops/d3-reconciliation-walkthrough.md
  prerequisite_reviews:
    - docs/ops/stage-e-broker-live-scoping-prerequisites.md
    - docs/ops/stage-e-broker-live-prerequisite-gap-review.md
    - docs/ops/broker-no-submit-evidence-review.md
  local_artifacts:
    - outputs/hyperliquid_submits
    - outputs/hyperliquid_submits/hyperliquid_submits_health.json
```

## State Model Used

The pack uses the operator vocabulary from
`docs/ops/d3-reconciliation-walkthrough.md`:

```yaml
state_model:
  submitted_remote:
    meaning: "Venue submit happened and remote order existence must be reconciled."
  filled:
    meaning: "Order status/fill evidence reports a fill."
  closed:
    meaning: "Evidence supports no remaining exposure for the reviewed order lifecycle."
  submit_rejected:
    meaning: "Venue rejected the submit before a remote order lifecycle was established."
  missing_order_identifier:
    meaning: "No oid/cloid is available for remote status lookup."
  unknown:
    meaning: "Remote state is not known from available artifacts."
  ambiguous:
    meaning: "Evidence conflicts or is insufficient for safe classification."
```

Operational rule:

```yaml
rule:
  - "Known submitted_remote sessions require order-status and reconciliation evidence."
  - "Rejected sessions must not be treated as filled or closed."
  - "Missing order identifiers are terminal for the rejected-submit diagnostic, but remain a stop condition for any session that is assumed to have remote exposure."
  - "Unknown or ambiguous state remains stop, not retry."
```

## Artifact Inventory

Existing local submit root:

```yaml
artifact_root:
  path: outputs/hyperliquid_submits
  exists: true
```

Aggregate health snapshot:

```yaml
health:
  total_sessions: 8
  submitted_sessions: 2
  submit_rejected_sessions: 6
  reconciliation_sessions: 7
  fill_summary_sessions: 7
  supervision_sessions: 2
  order_status_known_sessions: 2
  submit_state_counts:
    submitted_remote: 2
    submit_rejected: 6
  order_state_counts:
    filled: 2
    unknown: 6
  fill_state_counts:
    filled: 2
    unknown: 6
  close_state_counts:
    closed: 2
    unknown: 6
  alert_status: critical
  latest_issue_code: HYPERLIQUID_SUBMIT_REJECTED
  latest_issue_session_id: 20260514_172736_hyperliquid_submit_70d57e2
```

Interpretation:

- The artifact set contains enough evidence to classify the two submitted
  sessions as known filled/closed lifecycle evidence.
- The six rejected sessions remain retained critical historical evidence.
- Critical root alert status is not hidden or downgraded by this pack.

## Session Reconciliation Matrix

```yaml
sessions:
  20260430_215047_hyperliquid_submit_9dee959:
    submit_state: submit_rejected
    submitted: false
    remote_submit_called: true
    reconciliation_artifact: present
    reconciliation_state: unknown
    status_known: false
    errors:
      - missing_order_identifier
    classification: rejected_without_remote_order_identifier
    operator_rule: "Record as rejected; do not infer fill or close; no retry."

  20260502_203655_hyperliquid_submit_e23957f:
    submit_state: submit_rejected
    submitted: false
    remote_submit_called: true
    reconciliation_artifact: present
    reconciliation_state: unknown
    status_known: false
    classification: rejected_without_remote_order_identifier
    operator_rule: "Record as rejected; do not infer fill or close; no retry."

  20260502_212817_hyperliquid_submit_8dc7bb4:
    submit_state: submit_rejected
    submitted: false
    remote_submit_called: true
    order_status_known: false
    reconciliation_artifact: present
    reconciliation_state: unknown
    status_known: false
    classification: rejected_without_known_remote_order
    operator_rule: "Record as rejected; missing remote status means stop, not retry."

  20260502_221518_hyperliquid_submit_acb15e7:
    submit_state: submit_rejected
    submitted: false
    remote_submit_called: true
    reconciliation_artifact: present
    reconciliation_state: unknown
    status_known: false
    classification: rejected_without_remote_order_identifier
    operator_rule: "Record as rejected; do not infer fill or close; no retry."

  20260502_230137_hyperliquid_submit_7209d49:
    role: "D.3 entry evidence anchor"
    submit_state: submitted_remote
    submitted: true
    remote_submit_called: true
    order_status_known: true
    reconciliation_artifact: present
    reconciliation_state: filled
    fill_state: filled
    close_state: closed
    status_known: true
    resolution_source: order_status
    oid: 407946609357
    filled_size: "0.005"
    average_fill_price: "2323.5"
    fill_count: 1
    supervision_artifact: present
    classification: submitted_remote_filled_closed
    operator_rule: "Known remote lifecycle; continue only to evidence review."

  20260502_232513_hyperliquid_submit_5d599f8:
    role: "D.3 reduce-only close evidence anchor"
    submit_state: submitted_remote
    submitted: true
    remote_submit_called: true
    order_status_known: true
    reconciliation_artifact: present
    reconciliation_state: filled
    fill_state: filled
    close_state: closed
    status_known: true
    resolution_source: order_status
    oid: 407964084992
    filled_size: "0.005"
    average_fill_price: "2320.7"
    fill_count: 1
    supervision_artifact: present
    classification: submitted_remote_filled_closed
    operator_rule: "Known remote lifecycle; continue only to evidence review."

  20260514_090121_hyperliquid_submit_8ae1921:
    submit_state: submit_rejected
    submitted: false
    remote_submit_called: true
    reconciliation_artifact: present
    reconciliation_state: unknown
    status_known: false
    classification: rejected_without_remote_order_identifier
    operator_rule: "Record as rejected; do not infer fill or close; no retry."

  20260514_172736_hyperliquid_submit_70d57e2:
    role: "#800 rejected-submit diagnostic anchor"
    submit_state: submit_rejected
    submitted: false
    remote_submit_called: true
    order_status_known: false
    order_status_message: missing_order_identifier
    reconciliation_artifact: missing
    fill_summary_artifact: missing
    classification: rejected_without_order_identifier
    operator_rule: "Classified as rejected diagnostic evidence; no retry, no close, Stage E remains blocked."
```

## Positive Reconciliation Evidence

The strongest reconciliation evidence is the D.3 entry/close pair:

```yaml
positive_evidence:
  entry_session:
    session_id: 20260502_230137_hyperliquid_submit_7209d49
    normalized_state: filled
    fill_state: filled
    close_state: closed
    status_known: true
    resolution_source: order_status

  reduce_only_close_session:
    session_id: 20260502_232513_hyperliquid_submit_5d599f8
    normalized_state: filled
    fill_state: filled
    close_state: closed
    status_known: true
    resolution_source: order_status
```

These sessions prove that existing artifacts can represent:

- a submitted remote lifecycle,
- known order status,
- fill evidence,
- close evidence,
- supervision evidence.

## Rejected Session Evidence

Rejected sessions are not positive broker-readiness evidence. They are retained
failure evidence and must remain visible.

```yaml
rejected_evidence:
  count: 6
  common_state:
    submit_state: submit_rejected
    submitted: false
    remote_submit_called: true
  interpretation:
    - "Do not infer fills."
    - "Do not infer successful close."
    - "Do not retry."
    - "Preserve as critical historical evidence."
```

#800 remains the most important rejected-submit diagnostic anchor:

```yaml
issue_800:
  session_id: 20260514_172736_hyperliquid_submit_70d57e2
  classification: rejected_without_order_identifier
  reconciliation_artifact: missing
  expected_reason: "No oid/cloid was returned after rejected submit."
  related_postmortem: docs/ops/d3-issue-812-rejected-submit-postmortem.md
```

## Stop Conditions Confirmed

```yaml
stop_conditions:
  missing_order_identifier:
    rule: "Stop. Do not retry or assume remote state."

  status_known_false:
    rule: "Stop unless the session is already classified as rejected diagnostic evidence."

  reconciliation_artifact_missing:
    rule: "Stop for any submitted_remote session. For #800, record as expected rejected-submit limitation."

  root_alert_critical:
    rule: "Stop any Stage E discussion until alert cause is explainable and retained."
```

## Reconciliation Evidence Decision

```yaml
decision:
  reconciliation_evidence:
    status: satisfied
    scope: static_stage_e_prerequisite_evidence_pack
    reason:
      - "All existing submit sessions were inventoried."
      - "The two submitted_remote sessions have order-status, reconciliation, fill, close, and supervision evidence."
      - "Rejected sessions are classified separately and are not treated as fills."
      - "#800 is classified as rejected without order identifier and remains a no-retry diagnostic anchor."
      - "Unknown/missing-order states are explicitly documented as stop conditions."

  broker_readiness:
    status: not_ready
    reason:
      - retained_critical_rejected_submit_evidence
      - stop_control_dry_drill_missing
      - artifact_durability_review_missing

  stage_e:
    remains_blocked: true
```

This pack satisfies the reconciliation evidence gap for the #830/#832 Stage E
prerequisite review. It does not make Stage E scopeable by itself.

## Remaining Gaps

```yaml
remaining_gaps:
  stop_control_dry_drill:
    title: "ops(broker): run stop-control dry drill against existing artifacts"

  artifact_durability_review:
    title: "ops(stage-e): verify broker evidence artifact durability"
```

## Final Boundary

Do not use this evidence pack to authorize Stage E, broker submit, live capital,
signed action generation, cancel, close, runtime changes, Stepbit, or retry of
any rejected session.
