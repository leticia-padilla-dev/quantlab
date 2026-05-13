# D.3 Operator Hardening Declarations

Issue: [#669](https://github.com/Whiteks1/quantlab/issues/669)

Status: `partial_operator_signature_recorded`

This document records the declarations required before Stage E can be considered for a separate scoping issue.

It does not open Stage E, authorize live expansion, authorize automation, or authorize broker submit from Desktop.

## Source Gate

Required by:

- [D.3 Hardening and Stage E Promotion Criteria](../d3-hardening-and-promotion-criteria.md)
- [Supervised Broker Runbook](../supervised-broker-runbook.md)
- [Supervised Paper Operation Readiness Audit](./supervised-paper-readiness-audit.md)

## Evidence Paths

Entry session:

```text
outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49
```

Reduce-only close session:

```text
outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8
```

## Declaration Status

```yaml
stage_e: blocked
operator_declarations_complete: false
declaration_owner: operator
record_created_by: Codex
record_status: partial_operator_signature_recorded
last_signature_date: "2026-05-13"
last_signature: "Leti / Whiteks1 — signed"
```

## Required Declarations

The operator must explicitly confirm all five declarations below.

### 1. Runbook Reconstruction

Required declaration:

```text
I can reconstruct the Hyperliquid entry and reduce-only close flows using only the supervised broker runbook, without consulting #446 session history.
```

References:

- `docs/supervised-broker-runbook.md` § 5
- `docs/supervised-broker-runbook.md` § 6.5

Status:

```yaml
confirmed: true
operator_signature: "Leti / Whiteks1 — signed"
signature_date: "2026-05-13"
```

### 2. Alert Aggregation Understanding

Required declaration:

```text
I understand the alert aggregation model: root-level `critical` can coexist with latest-session `ok`, because historical rejected sessions remain preserved as evidence.
```

References:

- `docs/supervised-broker-runbook.md` § 11 health note
- `outputs/hyperliquid_submits/hyperliquid_submits_health.json`
- `outputs/hyperliquid_submits/hyperliquid_submits_alerts.json`

Status:

```yaml
confirmed: true
operator_signature: "Leti / Whiteks1 — signed"
signature_date: "2026-05-13"
```

### 3. Reconciliation State Understanding

Required declaration:

```text
I can explain the reconciliation states `submitted_remote`, `reconciliation_required`, and `filled`, and I understand that unclear reconciliation means stop rather than open another session.
```

References:

- `outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49/hyperliquid_reconciliation.json`
- `docs/d3-hardening-and-promotion-criteria.md` § 4.3

Status:

```yaml
confirmed: true
operator_signature: "Leti / Whiteks1 — signed"
signature_date: "2026-05-13"
```

### 4. Stop-Control Understanding

Required declaration:

```text
I understand that reduce-only close is the correct stop-control mechanism for a filled perp position, and that emergency UI close is a fallback of last resort only when QuantLab artifacts are unavailable or ambiguous.
```

References:

- `docs/supervised-broker-runbook.md` § 6
- `docs/supervised-broker-runbook.md` § 6.5
- `docs/supervised-broker-runbook.md` § 12
- `outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/hyperliquid_reconciliation.json`

Status:

```yaml
confirmed: true
operator_signature: "Leti / Whiteks1 — signed"
signature_date: "2026-05-13"
```

### 5. Evidence Trail Durability

Required declaration:

```text
The D.3 entry and reduce-only close session directories exist locally, are readable, and have not been intentionally modified since cycle completion.
```

References:

- `outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49`
- `outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8`

Status:

```yaml
confirmed: false
operator_signature: pending
```

## Stage E Decision Rule

Stage E remains blocked until:

1. All five declarations above are confirmed by the operator.
2. The confirmations are recorded in this document or a follow-up declaration issue.
3. A separate Stage E scoping issue is opened explicitly.

Closing this document alone must not open Stage E.

## Frozen Tracks

```yaml
blocked:
  - Stage_E
  - automation
  - new_venues
  - broker_submit_from_Desktop
  - Stepbit_61
```
