# Paper → Promotion: Deterministic Handoff Artifact Specification

Issue: [#763](https://github.com/Whiteks1/quantlab/issues/763)

Status: spec + report-only tooling. No broker actions. No submit. Stage E remains blocked.

## Purpose

Define a deterministic, paper-derived handoff artifact that:

- is built only from existing paper session artifacts
- is auditable and reviewable
- carries no execution authority
- can be validated locally with deterministic rules

This artifact exists to support governed promotion discussions without turning paper into proto-live.

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Contract

```yaml
artifact_type: quantlab.paper.promotion_handoff
artifact_version: "1.0"
```

## Inputs

Source session directory:

```text
outputs/paper_sessions/<session_id>/
```

Authoritative required inputs:

- `session_metadata.json`
- `session_status.json`
- `report.json`
- `trades.csv`

## Output Location (Default)

Default output location is the source session directory:

```text
outputs/paper_sessions/<session_id>/paper_promotion_handoff.json
outputs/paper_sessions/<session_id>/paper_promotion_handoff_validation.json
```

## Schema (High-Level)

```yaml
artifact_type: quantlab.paper.promotion_handoff
artifact_version: "1.0"
generated_at: "<iso>"

source:
  session_id: "<paper_session_id>"
  session_dir: "<path>"

constraints:
  submit_allowed: false
  stage_e: blocked
  execution_authority: "none"

canonical_summary:
  status: "<success|failed|aborted|running|unknown>"
  terminal: "<bool>"
  status_reason: "<string>"
  request_id: "<string|null>"
  report_contract_type: "<string|null>"

artifact_paths:
  session_metadata_json: "<path>"
  session_status_json: "<path>"
  report_json: "<path>"
  trades_csv: "<path>"

artifact_presence:
  session_metadata_json: "<bool>"
  session_status_json: "<bool>"
  report_json: "<bool>"
  trades_csv: "<bool>"

handoff_readiness:
  handoff_allowed: "<bool>"
  blockers: ["<string>"]
  reasons: ["<string>"]
```

## Deterministic Validation Rules

The validator must reject if:

- contract_type/version mismatch
- `source.session_dir` does not exist
- required_minimum artifacts are missing (presence == false)

The validator must compute `handoff_allowed` deterministically from:

- terminality + status + report contract

## Non-Goals

- This artifact does not authorize broker actions.
- This artifact does not open Stage E.
- This artifact does not grant promotion authority.
- This artifact is not a strategy performance report.
