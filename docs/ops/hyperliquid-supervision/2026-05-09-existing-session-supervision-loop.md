# Hyperliquid Supervision Evidence — Existing Session Loop

Issue: [#670](https://github.com/Whiteks1/quantlab/issues/670)

## Metadata

```yaml
date: 2026-05-09
source_session_id: 20260502_232513_hyperliquid_submit_5d599f8
mode: existing_session_supervision
operator: marce
new_submit: false
source_issue: 670
```

## Objective

Demonstrate that the Hyperliquid supervision artifact loop can operate on an existing D.3 session without creating a new submit.

## Command

```powershell
.\.venv\Scripts\python.exe main.py --hyperliquid-submit-sessions-supervise outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8
```

## CLI Result

```text
Hyperliquid submit supervision completed:

  session_path        : outputs\hyperliquid_submits\20260502_232513_hyperliquid_submit_5d599f8
  supervision_path    : outputs\hyperliquid_submits\20260502_232513_hyperliquid_submit_5d599f8\hyperliquid_supervision.json
  supervision_state   : terminal
  polls_completed     : 1
  effective_state     : filled
  fill_state          : filled
  alert_status        : ok
  alert_counts        : {}
```

## Supervision Artifact

Path:

```text
outputs/hyperliquid_submits/20260502_232513_hyperliquid_submit_5d599f8/hyperliquid_supervision.json
```

Key fields:

```json
{
  "artifact_type": "quantlab.hyperliquid.supervision",
  "attention_required": false,
  "ended_early": true,
  "errors": [],
  "final_close_state": "closed",
  "final_fill_count": 1,
  "final_fill_state": "filled",
  "final_order_state": "filled",
  "final_reconciliation_state": "filled",
  "final_remaining_size": "0",
  "polls_completed": 1,
  "polls_requested": 3,
  "private_websocket_implemented": false,
  "resolved_transport": "websocket",
  "source_session_id": "20260502_232513_hyperliquid_submit_5d599f8",
  "supervision_state": "terminal",
  "transport_preference": "websocket"
}
```

## Aggregate Health After Supervision

```text
Hyperliquid submission health: outputs\hyperliquid_submits

  total_sessions          : 6
  submitted_sessions      : 2
  order_status_known      : 2
  reconciliation_sessions : 6
  latest_close_state      : closed
  latest_fill_state       : filled
  latest_supervision_state: terminal
  alert_status            : critical
  alert_counts            : {'critical': 4}
  latest_submit_id        : 20260502_232513_hyperliquid_submit_5d599f8
  latest_submit_state     : submitted_remote
  latest_order_state      : filled
  latest_reconcile_state  : filled
```

## Aggregate Alerts After Supervision

```yaml
alert_status: critical
alert_counts:
  critical: 4
supervision_sessions: 1
latest_alert_code: HYPERLIQUID_SUBMIT_REJECTED
latest_alert_session_id: 20260502_221518_hyperliquid_submit_acb15e7
```

## Interpretation

The supervision artifact loop is now demonstrated for an existing D.3 close session.

The latest supervised session is terminal, filled, reconciled, closed, and does not require attention.

The root aggregate remains `critical` because historical rejected sessions are preserved. This is expected and should not be interpreted as the latest supervised session failing.

## Result

```yaml
supervision_artifact_created: true
supervision_sessions_after: 1
new_submit_performed: false
latest_session_terminal: true
latest_session_attention_required: false
root_alert_status: critical
root_alert_reason: historical_rejected_sessions
```

## Boundary

- No new submit occurred.
- No close/retry/cancel occurred.
- No Stage E scope opened.
- No automation occurred.
- No Stepbit work occurred.
