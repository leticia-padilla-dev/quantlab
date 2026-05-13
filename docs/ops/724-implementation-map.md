# Implementation Map — Tracking Block #724

Issue: #724

Status: execution order + guardrails. Docs-only.

Rule: do not mix Track A (page) with Track B (D.3 hardening).

## Track A — Page / Local Preview

### #717 — feat(web): add local preview workflow for QuantLab page

Allowed scope (expected):

- `landing/`
- `.github/workflows/*` if needed for local preview workflow
- `docs/landing-governance.md` if governance text needs an update

Hard boundary:

- Must not touch `src/quantlab/` runtime or `docs/ops/` D.3 hardening files in the same PR.

## Track B — D.3 Hardening / Operational Confidence (Docs-First)

Execution order:

1. #718 — runbook-only reconstruction drill without submit (docs-only)
2. #719 — reconciliation state walkthrough and glossary (docs-only)
3. #720 — stop-control decision table and drill memo (docs-only)
4. #721 — restart/resume posture decision and operator rules (docs-only)
5. #722 — paper session heartbeat (runtime optional; only after #721)
6. #723 — supervised paper/live re-audit (must remain open until drill memos exist)

### #718 — ops(d3): runbook-only reconstruction drill without submit

Expected output:

- `docs/ops/d3-runbook-reconstruction-drill.md`
- Operator memo under `docs/ops/` (no submit, no broker action).

### #719 — ops(d3): reconciliation state walkthrough and glossary

Expected output:

- `docs/ops/d3-reconciliation-walkthrough.md`
- Operator memo under `docs/ops/` that demonstrates state interpretation from existing artifacts.

### #720 — ops(d3): stop-control decision table and drill memo

Expected output:

- `docs/ops/d3-stop-control-drill.md`
- Operator memo under `docs/ops/` that applies the table (cancel vs reduce-only close vs emergency UI).

### #721 — ops(paper): restart/resume posture decision and operator rules

Expected output:

- `docs/ops/paper-restart-resume-posture.md`

Hard boundary:

- This is the governance gate for any optional runtime hardening in #722.

### #722 — paper(runtime): add paper session heartbeat to reduce false-stale alerts

Scope guardrails:

- Paper sessions only (no broker changes).
- Allowed file scope:
  - `src/quantlab/cli/run.py`
  - `test/test_paper_session.py`

### #723 — ops: supervised paper/live pack re-audit after D3 drills

Gate:

- Do not close #723 until #718–#721 are completed and the drill memos exist.
- A re-audit document may exist early as `still_blocked`, but it must not be used to claim readiness.

## Cross-Cutting

### #669 — D.3 operator hardening declarations

Authority:

- `docs/ops/d3-operator-hardening-declarations.md`

Note:

- No doc addition closes #669. It requires explicit operator confirmation.

