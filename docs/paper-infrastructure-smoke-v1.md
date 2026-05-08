# Paper Infrastructure Smoke v1

## Purpose

Validate that the paper session infrastructure works before a strategy trial begins.

This is `paper_infrastructure_smoke` mode. It does **not** require:
- A research pass
- A baseline candidate
- A candidate memo
- Stop conditions

It does require a dummy, fixture, or safe test config — not a research candidate.

A successful infrastructure smoke confirms:
- Session lifecycle starts and terminates cleanly
- Artifacts are written to expected paths
- Logs are recoverable
- Simulated reconciliation runs without errors
- Session status is observable throughout

A failed infrastructure smoke blocks `paper_strategy_trial` until resolved.

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| Config | Dummy strategy, fixture config, or safe test config only |
| Research pass | Not required |
| Baseline candidate | Not required |
| Stop conditions | Not required (session is controlled duration) |
| Candidate memo | Not required |

---

## Smoke Session Checklist

Run through this checklist during the smoke session:

### Session Lifecycle

- [ ] Session starts without errors
- [ ] Session runs for intended duration without hanging
- [ ] Session terminates with an explicit status (`complete` / `stopped` / `failed`)
- [ ] Session status is observable during execution (not only visible at end)

### Artifacts

- [ ] `report.json` written to `outputs/runs/<run_id>/`
- [ ] Session log written and readable
- [ ] Simulated order record exists (even if empty for dummy strategy)
- [ ] Artifact paths match expected structure

### Logs

- [ ] Logs are recoverable after session ends
- [ ] No silent log failures
- [ ] Timestamps are consistent

### Simulated Reconciliation

- [ ] Reconciliation runs without crashing
- [ ] Reconciliation produces output (does not need to show balance)
- [ ] No unresolved reconciliation errors

---

## What Infrastructure Smoke Does NOT Validate

- Strategy correctness or signal quality
- PnL or return metrics
- Benchmark comparison
- Whether the strategy is a candidate for promotion
- Any research evidence

Results from an infrastructure smoke session may NOT be used to support:
- Candidate promotion
- D.3 review
- Baseline candidate declaration
- Strategy decision of any kind

---

## Session Record Template

After completing a smoke session, record the result here:

```
paper_infrastructure_smoke_v1:
  date: <YYYY-MM-DD>
  config_used: <dummy/fixture config name>
  run_id: <run_id or 'local-only'>
  lifecycle_pass: <true/false>
  artifacts_pass: <true/false>
  logs_pass: <true/false>
  reconciliation_pass: <true/false>
  overall_status: <pass/fail>
  notes: <any observations>
  blocker_for_strategy_trial: <none / describe if fail>
```

---

## Outcome States

| Status | Meaning | Next step |
|--------|---------|-----------|
| `pass` | All checklist items passed | Infrastructure confirmed; strategy trial may proceed when other gates pass |
| `fail` | One or more checklist items failed | Fix the infrastructure issue; re-run smoke before strategy trial |
| `partial` | Some items passed but reconciliation or artifacts incomplete | Treat as fail; investigate before proceeding |

A `partial` is never acceptable as a gate pass. Resolve before `paper_strategy_trial`.

---

## Separation from Strategy Trial

Infrastructure smoke results are **not** strategy trial results.

Do not combine infrastructure smoke sessions with research candidate configs.
Do not record infrastructure smoke PnL or signal behavior as strategy evidence.
Do not reference infrastructure smoke results in candidate memos.
