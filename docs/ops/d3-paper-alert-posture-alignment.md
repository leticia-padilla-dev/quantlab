# D.3: How Paper Alert Posture Influences D.3 Interpretation

Issue: [#781](https://github.com/Whiteks1/quantlab/issues/781)

Status: docs-only. No runtime changes. No submit. Stage E remains blocked.

## Purpose

QuantLab uses paper operations as the promotion floor for supervised micro-live work.

This document defines:

- how paper alert posture is interpreted in a D.3 context
- what actions are permitted when posture is critical/warning/ok
- how to preserve evidence without greenwashing historical failures

## Stage E Boundary (Must Remain True)

```yaml
stage_e:
  status: blocked
  submit_allowed: false
  runtime_open: false
```

## Inputs

Paper alert posture is produced by:

```bash
python main.py --paper-sessions-alerts outputs/paper_sessions \
  --paper-stale-minutes 60 \
  --paper-alert-window-days 7 \
  --paper-alert-window-sessions 20
```

Two layers are always present:

- historical posture over all sessions:
  - `alert_status` / `alerts[]`
- current operational window posture (horizon filtered):
  - `current_window_alert_status` / `current_window_alerts[]`

Operator interpretation rules:

- [paper-alert-posture-interpretation-rules.md](./paper-alert-posture-interpretation-rules.md)

Governing policy:

- [paper-failure-retention-and-alert-horizon-policy.md](./paper-failure-retention-and-alert-horizon-policy.md)

## D.3 Interpretation Principle

Paper alert posture does not authorize broker actions.

Instead, paper posture is used as a D.3 safety signal:

- if the current paper window is unhealthy, do not proceed into new D.3 broker-facing evidence work
- historical failures remain visible as learning evidence and must not be deleted or hidden

## Decision Table (D.3 Alignment)

The table below maps paper posture to allowed D.3 actions.

| paper posture | meaning (D.3) | allowed actions | forbidden actions |
|---|---|---|---|
| current_window `critical` | paper floor is currently unhealthy | stop; classify the implicated paper sessions using canonical artifacts; record posture snapshot as evidence | any D.3 submit; any “try again” loop; any attempt to fix posture by deleting failures |
| current_window `warning` | paper floor is degraded/ambiguous | stop and classify; document whether warning is operational noise or real break; do not proceed to D.3 broker evidence until classification is resolved | any D.3 submit; automation; ignoring warnings “because historical is already critical” |
| current_window `ok` and historical `critical` | current floor is healthy but history contains failures (expected) | proceed with paper evidence capture; proceed with docs-only D.3 hardening; broker-facing work remains gated by the supervised broker runbook and D.3 policies | greenwashing history; treating historical critical as “irrelevant” or “fixed” |
| current_window `ok` and historical `ok` | strong evidence of stable paper floor | proceed with paper evidence capture; proceed with supervised D.3 hardening work when explicitly authorized | any Stage E interpretation; any broker expansion |

## Required Evidence When Stopping

If the decision is to stop (critical/warning), the operator must preserve:

- the full alert snapshot JSON (including `horizon` and current window fields)
- the canonical per-session artifacts for each implicated session_id

Minimum canonical artifacts:

- `outputs/paper_sessions/<session_id>/session_status.json`
- `outputs/paper_sessions/<session_id>/session_metadata.json`
- `outputs/paper_sessions/<session_id>/report.json` (when status is success)

## Non-Goals

- This does not redefine D.3 broker runbook gates.
- This does not open Stage E.
- This does not authorize remediation automation or retries.
