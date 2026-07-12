
# External Consumer Local Invocation Contract

Historical source: [#552](https://github.com/leticia-padilla-dev/quantlab/issues/552)

Status: consumer contract for local external consumer integration.

Related evidence:

- [JSON request contract verification](./json-request-contract-verification.md)
- [External Consumer I/O contract v1](./external-consumer-io-v1.md)

## Purpose

This document defines the QuantLab-side local invocation contract that any external consumer is allowed to consume.

External consumers may invoke QuantLab through a narrow CLI boundary and read canonical artifacts. External consumers must not rely on QuantLab internals, private Python modules, Desktop renderer state, broker state, or implementation-specific stdout text.

## Authority Boundary

QuantLab remains the authority for:

- research execution
- strategy logic
- metrics
- reports
- canonical artifacts
- broker/live/paper boundaries
- promotion decisions

External consumers are external consumers. They may request a bounded action and inspect the resulting artifacts, but they do not own QuantLab lifecycle, execution policy, risk policy, broker submission, or strategy promotion.

Explicit exclusions:

- no broker submit
- no live trading
- no autonomous execution
- no external-consumer-owned promotion policy
- no parsing of private QuantLab internals
- no dependency on Desktop UI state

## Invocation

External consumers should invoke QuantLab with an explicit project interpreter from the QuantLab repository root.

Windows:

```powershell
.\.venv\Scripts\python.exe main.py --json-request $jsonRequest --signal-file $signalFile
```

POSIX:

```bash
./.venv/bin/python main.py --json-request "$jsonRequest" --signal-file "$signalFile"
```

Do not assume that global `python` has QuantLab dependencies installed.

The verified Windows interpreter was:

```powershell
.\.venv\Scripts\python.exe
```

The global interpreter failed verification due to missing project dependencies:

```text
ModuleNotFoundError: No module named 'dotenv'
```

## Request Envelope

All local requests use the JSON request envelope accepted by `main.py --json-request`.

```json
{
  "schema_version": "1.0",
  "request_id": "req_001",
  "command": "run",
  "params": {}
}
```

Fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `schema_version` | string | yes | Must be `"1.0"`. |
| `request_id` | string | recommended | Caller-generated correlation ID. Propagated into signals and `report.json.machine_contract`. |
| `command` | string | yes | Supported values for this contract: `run`, `sweep`. |
| `params` | object | yes | Command-specific parameters mapped to QuantLab CLI args. |

## Run Request

Use `command: "run"` for a single QuantLab research run.

Required `params`:

| Field | Type | Description |
|---|---|---|
| `ticker` | string | Market symbol, for example `"ETH-USD"`. |
| `start` | string | Inclusive start date, `YYYY-MM-DD`. |
| `end` | string | Exclusive or run-defined end date, `YYYY-MM-DD`. |

Optional `params`:

| Field | Type | Description |
|---|---|---|
| `interval` | string | Data interval. Verified with `"1d"`. |
| `initial_cash` | number | Initial cash if supported by the run path. |
| `paper` | boolean | Executes the paper-session path when true. Not required for research run integration. |
| `report` | boolean | Requests report generation where supported. |

Current output behavior:

- Plain `run` writes under `outputs/runs/&lt;run_id&gt;/`.
- Plain `run` currently ignores `params.out_dir`.
- Paper-backed `run` writes under `outputs/paper_sessions/&lt;session_id&gt;/` and is outside the required #552 research integration path.

PowerShell example:

```powershell
$signalFile = "$env:TEMP\quantlab-external\run-signals.jsonl"
$jsonRequest = @{
  schema_version = "1.0"
  request_id = "req_run_001"
  command = "run"
  params = @{
    ticker = "ETH-USD"
    start = "2022-01-01"
    end = "2023-12-31"
    interval = "1d"
  }
} | ConvertTo-Json -Compress -Depth 6

.\.venv\Scripts\python.exe main.py --json-request $jsonRequest --signal-file $signalFile
```

## Sweep Request

Use `command: "sweep"` for config-backed experiments and walk-forward/grid sweeps.

Required `params`:

| Field | Type | Description |
|---|---|---|
| `config_path` | string | Repository-relative path to a sweep config YAML/JSON file. |

Optional `params`:

| Field | Type | Description |
|---|---|---|
| `out_dir` | string | Parent output directory for the generated run directory. Verified. |
| `sweep_outdir` | string | Legacy-compatible alias for `out_dir`. |

PowerShell example:

```powershell
$sweepOut = "$env:TEMP\quantlab-external\sweep-outputs"
$signalFile = "$env:TEMP\quantlab-external\sweep-signals.jsonl"
$jsonRequest = @{
  schema_version = "1.0"
  request_id = "req_sweep_001"
  command = "sweep"
  params = @{
    config_path = "configs/experiments/eth_2023_grid.yaml"
    out_dir = $sweepOut
  }
} | ConvertTo-Json -Compress -Depth 6

.\.venv\Scripts\python.exe main.py --json-request $jsonRequest --signal-file $signalFile
```

## Signal File Contract

External consumers should provide a signal file path and consume it as JSON Lines.

Invocation:

```powershell
.\.venv\Scripts\python.exe main.py --json-request $jsonRequest --signal-file $signalFile
```

Format:

- append-only JSON Lines
- one JSON object per line
- best-effort writes
- lifecycle events are the primary process-level progress surface

Expected events:

| Event | Status | Meaning |
|---|---|---|
| `SESSION_STARTED` | `running` | QuantLab accepted the invocation and began work. |
| `SESSION_COMPLETED` | `success` | QuantLab completed and may include result paths. |
| `SESSION_FAILED` | `error` | QuantLab failed and should include error metadata. |

Common fields:

| Field | Description |
|---|---|
| `schema_version` | Signal schema version, usually `"1.0"`. |
| `event` | Lifecycle event name. |
| `status` | `running`, `success`, or `error`. |
| `mode` | Public command type such as `run` or `sweep`. |
| `request_id` | Propagated from the request envelope when supplied. |
| `timestamp` | Local timestamp emitted by QuantLab. |

Successful completion should include:

| Field | Description |
|---|---|
| `run_id` | Generated run/session identifier. |
| `artifacts_path` | Directory containing the generated artifacts. |
| `report_path` | Path to canonical `report.json`. |
| `summary` | Compatibility summary. Not authoritative. |

Example `SESSION_COMPLETED`:

```json
{
  "event": "SESSION_COMPLETED",
  "status": "success",
  "mode": "sweep",
  "request_id": "req_sweep_001",
  "run_id": "20260509_202930_grid_631fada",
  "artifacts_path": "C:\\Users\\marce\\AppData\\Local\\Temp\\quantlab-external\\sweep-outputs\\20260509_202930_grid_631fada",
  "report_path": "C:\\Users\\marce\\AppData\\Local\\Temp\\quantlab-external\\sweep-outputs\\20260509_202930_grid_631fada\\report.json",
  "summary": {
    "total_return": 0.20049373445085994,
    "sharpe_simple": 0.9470664730451578,
    "max_drawdown": -0.17333954698992726,
    "trades": 8,
    "win_rate": 0.5
  }
}
```

## Canonical Result Contract

The canonical machine-readable result is:

```text
report.json.machine_contract
```

External consumers should:

1. Wait for a `SESSION_COMPLETED` signal.
2. Require `report_path` to be present.
3. Read `report_path`.
4. Read `report.json.machine_contract`.
5. Treat `machine_contract` as authoritative.
6. Resolve artifact filenames relative to the directory containing `report.json`.

External consumers should not treat stdout text as the result contract. QuantLab currently does not emit a JSON response envelope to stdout.

### Machine Contract Fields

Common fields:

| Field | Description |
|---|---|
| `schema_version` | Machine contract schema version. |
| `contract_type` | Result type, for example `quantlab.run.result` or `quantlab.sweep.result`. |
| `command` | Original public command. |
| `status` | QuantLab result status. |
| `request_id` | Request correlation ID when supplied. |
| `run_id` | Generated run/session identifier. |
| `mode` | QuantLab execution mode such as `run` or `grid`. |
| `summary` | Canonical machine-facing KPI summary. |
| `artifacts` | Artifact name map relative to the report directory. |

Sweep contracts may also include:

| Field | Description |
|---|---|
| `best_result` | Best sweep row/result when available. |

Example run machine contract:

```json
{
  "schema_version": "1.0",
  "contract_type": "quantlab.run.result",
  "command": "run",
  "status": "success",
  "request_id": "req_run_001",
  "run_id": "20260509_182903_run_fb06467",
  "mode": "run",
  "summary": {
    "max_drawdown": -0.4126726449991832,
    "sharpe_simple": 0.0889590694172788,
    "total_return": -0.06981480778412885,
    "trades": 54,
    "win_rate": 0.46534653465346537
  },
  "artifacts": {
    "metadata": "metadata.json",
    "config": "config.json",
    "metrics": "metrics.json",
    "report": "report.json"
  }
}
```

## Artifact Resolution

Given:

```text
report_path = C:\dev\quantlab\outputs\runs\&lt;run_id&gt;\report.json
machine_contract.artifacts.metrics = metrics.json
```

Resolve:

```text
C:\dev\quantlab\outputs\runs\&lt;run_id&gt;\metrics.json
```

Do not resolve artifact names relative to the external consumer process working directory.

Common research artifacts:

- `metadata.json`
- `config.json`
- `metrics.json`
- `report.json`
- `run_report.md`

Common sweep artifacts may also include:

- `leaderboard.csv`
- `experiments.csv`
- `best_config.json`
- `config_resolved.yaml`

Walk-forward runs may also include robustness artifacts when generated:

- `robustness_verdict.json`
- `robustness_verdict.md`

## Exit Code Policy

Current documented exit codes:

| Code | Label | Meaning |
|---:|---|---|
| `0` | `SUCCESS` | Task completed normally. |
| `1` | `GENERAL_ERROR` | Unexpected crash or unhandled exception. |
| `2` | `INVALID_CONFIG` | JSON payload or CLI flags are invalid. |
| `3` | `DATA_ERROR` | OHLC data missing or invalid state. |
| `4` | `STRATEGY_ERROR` | Strategy-specific logic failure or parameter/runtime error. |

External consumers should combine exit code with the signal-file and `machine_contract` checks. A zero exit code alone is not enough to prove a usable result.

## Invalid Consumer States

External consumers must treat these states as invalid or failed, even if QuantLab exits with code `0`:

- no signal file was written
- no `SESSION_COMPLETED` or `SESSION_FAILED` event appears
- final `SESSION_COMPLETED` is missing `report_path`
- `report_path` does not exist
- `report.json` cannot be parsed as JSON
- `report.json.machine_contract` is missing
- `machine_contract.request_id` does not match the request when a request ID was supplied
- `machine_contract.status` is not `success`

Known current gap:

```text
A data-insufficient plain run can emit SESSION_COMPLETED with exit_code 0 but without run_id, artifacts_path, report_path, or summary.
```

Consumer rule:

```text
SESSION_COMPLETED without report_path is not a valid success state.
```

## Legacy Compatibility

Some top-level fields such as signal `summary` or top-level report summaries exist for compatibility.

They are not the authority for external consumers.

Use:

```text
report.json.machine_contract
```

Do not use compatibility summaries as the primary integration contract.

## Minimal Consumer Algorithm

```text
1. Build JSON request envelope.
2. Generate a unique request_id.
3. Choose an explicit QuantLab interpreter.
4. Choose a signal-file path controlled by the external consumer.
5. Invoke QuantLab from the QuantLab repository root.
6. Wait for process exit.
7. Read signal file JSON Lines.
8. If SESSION_FAILED exists, fail with its error metadata.
9. Find final SESSION_COMPLETED.
10. Require report_path.
11. Read report.json.
12. Require report.json.machine_contract.
13. Verify request_id if supplied.
14. Verify machine_contract.status == "success".
15. Resolve artifact names relative to report_path parent.
16. Return machine_contract and resolved artifact paths.
```
