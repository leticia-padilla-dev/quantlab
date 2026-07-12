# QuantLab JSON Request Contract Verification

Issue: [#551](https://github.com/Whiteks1/quantlab/issues/551)

Date: 2026-05-09

## Purpose

Verify the current `main.py --json-request` contract for local machine consumers such as external orchestrators or AI workflow systems.

This document is evidence only. It does not add a Stepbit adapter, change strategy logic, change promotion rules, or add broker/live behavior.

## Verdict

```yaml
json_request_contract_status:
  run:
    status: verified_with_gap
    canonical_result: report.json.machine_contract
    signal_file_success_paths: present
  sweep:
    status: verified
    canonical_result: report.json.machine_contract
    signal_file_success_paths: present
  consumer_model:
    stdout_json_envelope: not_available
    read_success_from:
      - signal_file SESSION_COMPLETED event
      - report.json.machine_contract
  next:
    - "#552 can document local invocation"
    - "#61 should consume report.json.machine_contract after #552"
```

## Runtime Note

The contract should be invoked with an explicit project interpreter.

Verified interpreter:

```powershell
.\.venv\Scripts\python.exe
```

Using the global Python interpreter failed before QuantLab startup because project dependencies were not available:

```text
ModuleNotFoundError: No module named 'dotenv'
```

This is not a contract failure, but it is important for external consumers: #552 should document interpreter resolution explicitly.

## Run Contract

### Verified Command

```powershell
$runSignal = "$env:TEMP\quantlab-551-json-request\run-signals-success.jsonl"
$runReq = @{
  schema_version = "1.0"
  request_id = "req_551_run_success_001"
  command = "run"
  params = @{
    ticker = "ETH-USD"
    start = "2022-01-01"
    end = "2023-12-31"
    interval = "1d"
  }
} | ConvertTo-Json -Compress -Depth 6

.\.venv\Scripts\python.exe main.py --json-request $runReq --signal-file $runSignal
```

### Result

```yaml
exit_code: 0
run_id: 20260509_182903_run_fb06467
artifacts_path: C:\dev\quantlab\outputs\runs\20260509_182903_run_fb06467
report_path: C:\dev\quantlab\outputs\runs\20260509_182903_run_fb06467\report.json
```

### Signal File

The success signal emitted:

```json
{
  "event": "SESSION_COMPLETED",
  "status": "success",
  "mode": "run",
  "request_id": "req_551_run_success_001",
  "run_id": "20260509_182903_run_fb06467",
  "artifacts_path": "C:\\dev\\quantlab\\outputs\\runs\\20260509_182903_run_fb06467",
  "report_path": "C:\\dev\\quantlab\\outputs\\runs\\20260509_182903_run_fb06467\\report.json",
  "summary": {
    "total_return": -0.06981480778412885,
    "sharpe_simple": 0.0889590694172788,
    "max_drawdown": -0.4126726449991832,
    "trades": 54,
    "win_rate": 0.46534653465346537
  }
}
```

### Machine Contract

`report.json.machine_contract` exists and is the canonical machine-facing result surface:

```json
{
  "schema_version": "1.0",
  "contract_type": "quantlab.run.result",
  "command": "run",
  "status": "success",
  "request_id": "req_551_run_success_001",
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

## Sweep Contract

### Verified Command

```powershell
$sweepOut = "$env:TEMP\quantlab-551-json-request\sweep-outputs"
$sweepSignal = "$env:TEMP\quantlab-551-json-request\sweep-signals.jsonl"
$sweepReq = @{
  schema_version = "1.0"
  request_id = "req_551_sweep_001"
  command = "sweep"
  params = @{
    config_path = "configs/experiments/eth_2023_grid.yaml"
    out_dir = $sweepOut
  }
} | ConvertTo-Json -Compress -Depth 6

.\.venv\Scripts\python.exe main.py --json-request $sweepReq --signal-file $sweepSignal
```

### Result

```yaml
exit_code: 0
run_id: 20260509_202930_grid_631fada
artifacts_path: C:\Users\marce\AppData\Local\Temp\quantlab-551-json-request\sweep-outputs\20260509_202930_grid_631fada
report_path: C:\Users\marce\AppData\Local\Temp\quantlab-551-json-request\sweep-outputs\20260509_202930_grid_631fada\report.json
```

### Signal File

The success signal emitted:

```json
{
  "event": "SESSION_COMPLETED",
  "status": "success",
  "mode": "sweep",
  "request_id": "req_551_sweep_001",
  "run_id": "20260509_202930_grid_631fada",
  "artifacts_path": "C:\\Users\\marce\\AppData\\Local\\Temp\\quantlab-551-json-request\\sweep-outputs\\20260509_202930_grid_631fada",
  "report_path": "C:\\Users\\marce\\AppData\\Local\\Temp\\quantlab-551-json-request\\sweep-outputs\\20260509_202930_grid_631fada\\report.json",
  "summary": {
    "total_return": 0.20049373445085994,
    "sharpe_simple": 0.9470664730451578,
    "max_drawdown": -0.17333954698992726,
    "trades": 8,
    "win_rate": 0.5
  }
}
```

### Machine Contract

`report.json.machine_contract` exists and is the canonical machine-facing result surface:

```json
{
  "schema_version": "1.0",
  "contract_type": "quantlab.sweep.result",
  "command": "sweep",
  "status": "success",
  "request_id": "req_551_sweep_001",
  "run_id": "20260509_202930_grid_631fada",
  "mode": "grid",
  "summary": {
    "max_drawdown": -0.17333954698992726,
    "sharpe_simple": 0.9470664730451578,
    "total_return": 0.20049373445085994,
    "trades": 8,
    "win_rate": 0.5
  },
  "artifacts": {
    "metadata": "metadata.json",
    "config": "config.json",
    "metrics": "metrics.json",
    "report": "report.json"
  }
}
```

The sweep contract also includes `best_result`.

## Consumer-Facing Notes

- Invoke QuantLab with an explicit interpreter, preferably the project venv.
- Do not parse stdout as the primary response contract.
- Treat the `SESSION_COMPLETED` signal as the lifecycle pointer to `report_path`.
- Treat `report.json.machine_contract` as the authoritative machine-facing result.
- Resolve artifact names relative to the directory containing `report.json`.
- `request_id` is propagated into both lifecycle signals and `machine_contract`.
- `sweep.params.out_dir` works and can point to a caller-controlled output root.
- Plain `run` currently ignores `params.out_dir` because the run path is fixed under `outputs/runs/`.

## Gaps / Blockers

### Gap 1: Global Python Is Not Sufficient

`python main.py ...` using the global interpreter failed due to missing dependencies. This should be handled by #552 with explicit local invocation guidance.

### Gap 2: Plain Run Data-Insufficient Case Emits Success Lifecycle

This command used too little history after indicator lookbacks:

```powershell
.\.venv\Scripts\python.exe main.py --json-request $runReq --signal-file $runSignal
```

with:

```json
{
  "command": "run",
  "params": {
    "ticker": "ETH-USD",
    "start": "2023-01-01",
    "end": "2023-04-01",
    "interval": "1d"
  }
}
```

Observed behavior:

```text
ERROR: No data remaining after applying indicators (need more history for lookbacks).
exit_code: 0
final_signal: SESSION_COMPLETED
missing: run_id, artifacts_path, report_path, summary
```

This does not block the verified success path, but it is a lifecycle correctness gap for consumers. External consumers should require `report_path` on success and treat a completed signal without `report_path` as invalid until QuantLab hardens this path.

## Recommendation For #552

#552 should document:

- interpreter resolution (`.\.venv\Scripts\python.exe` on Windows)
- the exact `run` and `sweep` request shapes above
- signal-file consumption
- `report.json.machine_contract` as canonical
- completed-without-`report_path` as an invalid consumer state
- no stdout JSON envelope in the current contract

## Validation

```powershell
git diff --check
.\.venv\Scripts\python.exe main.py --json-request <run_request> --signal-file <run_signal>
.\.venv\Scripts\python.exe main.py --json-request <sweep_request> --signal-file <sweep_signal>
```
