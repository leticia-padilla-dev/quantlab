
# External Consumer I/O Contract — Version 1.0

## Purpose

This document defines the formal communication contract between **any external consumer** (AI/workflow system, external orchestrator, etc.) and **QuantLab** (research and execution system).

For the concrete local invocation guide external consumers should implement against, see [external-consumer-local-invocation-contract.md](./external-consumer-local-invocation-contract.md).

QuantLab is a research-first, CLI-driven system that remains autonomous. This contract provides a stable, machine-readable wrapper for optional headless integration.

Each field and section is labeled with its current implementation status:

- `[done]` — implemented and stable in the current codebase
- `[planned]` — defined here but not yet implemented (tracked in linked issues)

> The published version of this document lives in `docs/external-consumer-io-v1.md`.

---

## 1. Invocation

External consumers invoke QuantLab as an external consumer via its CLI boundary.

```bash
<EXPLICIT_PYTHON_INTERPRETER> main.py --json-request '&lt;JSON_PAYLOAD&gt;'
```

**Recommended Configuration Examples:**
- **Windows**: `.venv\Scripts\python.exe`
- **POSIX**: `.venv/bin/python`

`[done]` — The `--json-request` flag is registered and parsed in `main.py`.

`[done]` — Runtime resolution has been hardened for local automated execution:
- `main.py` anchors `src/` into `sys.path`.
- `PROJECT_ROOT` is resolved from the entrypoint.
- Default `outdir` is anchored to the project root when not explicitly provided.

---

## 2. Request Schema (Input)

### JSON Fields

| Field | Type | Status | Description |
|---|---|---|---|
| `schema_version` | `string` | `[done]` | Must be `"1.0"`. Validated by `main.py`. |
| `request_id` | `string` | `[done]` | Caller-generated ID for tracking. Captured as `args._request_id`. |
| `command` | `string` | `[done]` | One of: `run`, `sweep`, `forward`, `portfolio`. |
| `params` | `dict` | `[done]` | Command-specific parameters mapped to CLI args. |

`[done]` `params` keys are mapped to argparse namespace attributes via `setattr` in `main.py`.

`[done]` `schema_version` validation and `request_id` propagation are implemented.

### `command: "sweep"` contract `[done]`

Required under `params`:

- `config_path` — non-empty string path to the sweep YAML file

Optional under `params`:

- `out_dir` — target parent directory for the generated run directory
- `sweep_outdir` — legacy-compatible alias for `out_dir`

Invalid or missing `config_path` fails deterministically with exit code `2`.

---

## 3. Response (Output)

### Current Behavior `[done]`

QuantLab writes artifacts to a mode-specific output directory upon completion. External consumers read results from these files.

QuantLab does **not** emit a JSON response envelope to stdout. This is by current design.

For `command: "run"`, a successful execution now writes a canonical run directory under
`outputs/runs/&lt;run_id&gt;/` and returns the resolved `run_id`, `artifacts_path`, and canonical
`report_path` through the existing session-completion context. Its canonical `report.json`
now also includes:

- `machine_contract.schema_version = "1.0"`
- `machine_contract.contract_type = "quantlab.run.result"`
- `machine_contract.command = "run"`
- `machine_contract.status`
- `machine_contract.request_id` when provided
- `machine_contract.run_id`
- `machine_contract.mode`
- `machine_contract.summary`
- `machine_contract.artifacts`

For plain `run`, the top-level `summary` block also mirrors the same core KPI values for compatibility, but `report.json.machine_contract` remains the canonical machine-facing result surface.

If `command: "run"` is invoked with `params.paper = true`, QuantLab now executes through a dedicated paper-session lifecycle and writes artifacts under:

```text
outputs/paper_sessions/&lt;session_id&gt;/
```

In that case:

- the external request contract still remains `command = "run"`
- lifecycle signalling still uses `mode = "run"` for compatibility
- the produced `report.json.machine_contract` identifies the result as `quantlab.paper.result`
- the returned `run_id` is the paper session identifier

Canonical paper-session artifacts currently include:

- `session_metadata.json`
- `session_status.json`
- `config.json`
- `metrics.json`
- `report.json`
- `trades.csv`
- `run_report.md`

For `command: "sweep"`, the canonical machine-readable artifact is `report.json`, and it includes:

- `machine_contract.schema_version = "1.0"`
- `machine_contract.contract_type = "quantlab.sweep.result"`
- `machine_contract.command = "sweep"`
- `machine_contract.status`
- `machine_contract.request_id` when provided
- `machine_contract.run_id`
- `machine_contract.mode`
- `machine_contract.summary`
- `machine_contract.best_result` when available
- `machine_contract.artifacts`

### JSON Response Envelope `[planned]`

A future version may emit a structured JSON envelope to stdout on completion.

**Example success shape:**
```json
{
  "schema_version": "1.0",
  "request_id": "req_550e8400",
  "status": "success",
  "run_id": "20260320_162100_run_a1b2c3d",
  "artifacts_path": "outputs/runs/20260320_162100_run_a1b2c3d",
  "summary": {
    "total_return": 0.45,
    "sharpe_simple": 1.82,
    "max_drawdown": -0.15,
    "trades": 12,
    "win_rate": 0.62
  }
}
```

**Example failure shape:**
```json
{
  "schema_version": "1.0",
  "request_id": "req_550e8400",
  "status": "error",
  "error": {
    "code": "DATA_ERROR",
    "message": "OHLC data missing for requested range"
  }
}
```

`[planned]` Response envelope tracked in [Issue #22](https://github.com/Whiteks1/quantlab/issues/22).

---

## 4. Session Signalling `[done]`

QuantLab supports optional, file-based session signalling to notify external consumers of lifecycle events without polling.

### Invocation
```bash
python main.py --json-request '...' --signal-file path/to/signals.jsonl
```

### Behavior
- **Format**: JSON Lines (one JSON object per line).
- **Mode**: Append-only.
- **Reliability**: Best-effort writes; signal failures do not abort the session.

### Event Models

#### Common Fields (All Events)
| Field | Type | Description |
|---|---|---|
| `schema_version` | `string` | Always `"1.0"`. |
| `event` | `string` | `SESSION_STARTED`, `SESSION_COMPLETED`, or `SESSION_FAILED`. |
| `status` | `string` | `running`, `success`, or `error`. |
| `mode` | `string` | The public command type (e.g., `run`, `sweep`). |
| `request_id` | `string` | Propagated from request if available. |
| `timestamp` | `string` | ISO 8601 local time. |

Compatibility note:

- `command: "run"` with `paper = true` still emits `mode = "run"` in signals so external consumers do not experience a breaking contract change
- paper-specific lifecycle can be inferred from the returned artifact path under `outputs/paper_sessions/` and from `report.json.machine_contract.contract_type = "quantlab.paper.result"`

#### SESSION_COMPLETED
Includes result location metadata (when available):
- `run_id`: Unique identifier for the run.
- `artifacts_path`: Directory containing the run artifacts.
- `report_path`: Path to the canonical `report.json`.
- `runs_index_json`: Refreshed registry artifact for `outputs/runs/` after successful `run`, `sweep`, and `forward`.

For paper-backed `run` executions:

- `run_id` is the paper session identifier
- `artifacts_path` points to `outputs/paper_sessions/&lt;session_id&gt;/`
- `runs_index_json` is not expected because paper sessions do not currently refresh the shared run registry

#### SESSION_FAILED
Includes failure metadata:
- `exit_code`: Numeric process exit code (1-4).
- `error_type`: Exception class name.
- `message`: Human-readable error description.

---

## 5. Exit Codes `[done]`

| Code | Label | Meaning |
|---|---|---|
| `0` | `SUCCESS` | Task completed normally. |
| `1` | `GENERAL_ERROR` | Unexpected crash or unhandled exception. |
| `2` | `INVALID_CONFIG` | JSON payload or CLI flags are invalid. |
| `3` | `DATA_ERROR` | OHLC data missing or invalid state (e.g. empty or unusable data). |
| `4` | `STRATEGY_ERROR` | Strategy-specific logic failure or parameter/runtime error. |

---

## 6. Artifact Paths `[done]`

The canonical machine-readable artifact for integration is **`report.json`**.

For session-oriented flows, it is expected inside the produced run/session directory.

- **Typical pattern**: `outputs/runs/&lt;run_id&gt;/report.json`

Canonical run artifact set for new `run`- and `sweep`-produced runs:

- `outputs/runs/&lt;run_id&gt;/metadata.json`
- `outputs/runs/&lt;run_id&gt;/config.json`
- `outputs/runs/&lt;run_id&gt;/metrics.json`
- `outputs/runs/&lt;run_id&gt;/report.json`

Successful `run`, `sweep`, and `forward` executions refresh the shared registry:

- `outputs/runs/runs_index.csv`
- `outputs/runs/runs_index.json`
- `outputs/runs/runs_index.md`

Legacy `meta.json` and `run_report.json` remain read-compatible only.

Paper-backed `run` executions currently use a distinct session root:

```text
outputs/paper_sessions/&lt;session_id&gt;/
  session_metadata.json
  session_status.json
  config.json
  metrics.json
  report.json
  trades.csv
  run_report.md
```

These paper-session artifacts are operationally distinct from the research run registry under `outputs/runs/`.

---

## 7. Health and Versioning `[done]`

QuantLab provides machine-verifiable flags for runtime validation.

| Flag | Status | Description |
|---|---|---|
| `--version` | `[done]` | Prints the current QuantLab version as a stable string. |
| `--check` | `[done]` | Prints a deterministic JSON health summary and exits `0` on success or `2` on runtime/config failure. |

`--check` currently reports:

- `status`
- `project_root`
- `main_path`
- `src_root`
- `interpreter`
- `venv_active`
- `quantlab_import`
- `python_version`
- `version`

---

## 8. Known Gaps → Follow-Up Issues

| Gap | Issue |
|---|---|
| JSON response envelope emitted to stdout | #22 |
| `strategy` param mapping in `run` command | #21 |
| Webhook delivery for signals | #25 (Deferred) |
