# Stage E Evidence Navigation Index (Operator Paths)

Issue: [#737](https://github.com/Whiteks1/quantlab/issues/737)

Date: 2026-05-13

Status: docs-only navigation index. No runtime changes.

## Purpose

Provide an operator-oriented index of the evidence paths used to review and supervise execution under Stage E constraints.

This index is meant to reduce ambiguity under review by making the “where do I look” question trivial.

## Global Rule (Must Remain True)

```yaml
stage_e:
  status: blocked
  docs_only_default: true
```

## Primary Session Anchors (D.3)

```yaml
anchors:
  entry_session:
    path: outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49
  reduce_only_close_session:
    path: outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8
```

## Operator Path Index

Each section lists:

1) the artifact family (what it represents)  
2) a canonical example path (where to find it)  
3) the minimum operator question it answers (why it exists)

### 1) signed_action

Artifact:

- `hyperliquid_signed_action.json`

Example:

```text
outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49/hyperliquid_signed_action.json
outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/hyperliquid_signed_action.json
```

Operator question:

```yaml
signed_action_answers:
  - "What exactly was signed?"
  - "Was the action constructed under the expected corridor and intent?"
```

### 2) submit_response

Artifacts:

- `hyperliquid_submit_response.json`
- `session_status.json`

Example:

```text
outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49/hyperliquid_submit_response.json
outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/hyperliquid_submit_response.json
```

Operator question:

```yaml
submit_response_answers:
  - "Did the exchange acknowledge the submit attempt?"
  - "Are identifiers present, or is reconciliation required?"
```

### 3) reconciliation

Artifact:

- `hyperliquid_reconciliation.json`

Example:

```text
outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49/hyperliquid_reconciliation.json
outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/hyperliquid_reconciliation.json
```

Operator question:

```yaml
reconciliation_answers:
  - "What is the normalized state (submitted_remote / reconciliation_required / filled / closed)?"
  - "Is the state unambiguous enough to proceed, or do we stop?"
```

### 4) fill_summary

Artifact:

- `hyperliquid_fill_summary.json`

Example:

```text
outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49/hyperliquid_fill_summary.json
outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/hyperliquid_fill_summary.json
```

Operator question:

```yaml
fill_summary_answers:
  - "What actually filled (size/price/fees) and what is the realized close evidence?"
```

### 5) alerts

Artifacts:

- `outputs/hyperliquid_submits/hyperliquid_submits_alerts.json`
- (session-local alerts should be interpreted via `session_status.json` and reconciliation artifacts)

Example:

```text
outputs/hyperliquid_submits/hyperliquid_submits_alerts.json
```

Operator question:

```yaml
alerts_answers:
  - "What is the root alert posture across all sessions?"
  - "Is root-level critical explained by preserved historical rejected sessions?"
```

### 6) health

Artifacts:

- `outputs/hyperliquid_submits/hyperliquid_submits_health.json`
- `outputs/hyperliquid_submits/hyperliquid_submits_index.json`
- `outputs/hyperliquid_submits/hyperliquid_submits_index.md`

Example:

```text
outputs/hyperliquid_submits/hyperliquid_submits_health.json
outputs/hyperliquid_submits/hyperliquid_submits_index.json
```

Operator question:

```yaml
health_answers:
  - "What is the aggregate state (counts, latest state, supervision sessions)?"
  - "Is the system stable enough for review without hiding critical evidence?"
```

### 7) supervision

Artifact:

- `hyperliquid_supervision.json` (when present)

Example:

```text
outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/hyperliquid_supervision.json
```

Operator question:

```yaml
supervision_answers:
  - "Was a supervision loop executed and recorded for this session?"
  - "What was the observed supervision state progression?"
```

### 8) reduce_only_close

Artifacts:

- `hyperliquid_signed_action.json`
- `hyperliquid_reconciliation.json`
- `session_status.json`

Example:

```text
outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/
```

Operator question:

```yaml
reduce_only_close_answers:
  - "Is this a reduce-only close flow, and is the final state closed?"
```

## Quick Navigation Shortcuts

```yaml
open_first:
  - outputs/hyperliquid_submits/hyperliquid_submits_health.json
  - outputs/hyperliquid_submits/hyperliquid_submits_alerts.json
  - outputs/hyperliquid_submits/20260502_230137_hyperliquid_submit_7209d49/hyperliquid_reconciliation.json
  - outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/hyperliquid_reconciliation.json
```

## Out of Scope

- No runtime changes.
- No automation.
- No Stepbit work.
- No venue expansion.
