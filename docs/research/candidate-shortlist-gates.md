# Candidate Shortlist Gates

## Purpose

A robustness PASS does not make a config a baseline candidate.
The shortlist gates are the intermediate review step between PASS and
baseline candidate declaration.

No config may be declared `baseline_candidate` without passing all shortlist gates.

---

## Entry Criteria (all must be true)

| Gate | Requirement |
|------|-------------|
| `robustness_verdict` | `pass` from a confirmatory run |
| `report_json_available` | `report.json` exists in `outputs/runs/<run_id>/` |
| `robustness_verdict_json_available` | `robustness_verdict.json` exists in `outputs/runs/<run_id>/` |
| `config_hash_locked` | `config_hash` recorded in config decision matrix before the run |
| `benchmark_comparison` | All four B01–B04 peers compared; `Benchmark` column is not `pending` or `blocked` |
| `no_manual_cherry_picking` | OOS splits were not redefined after seeing results |
| `candidate_memo_complete` | Operator has filled the candidate memo template (see below) |

If any gate fails, the config stays in REVIEW and may not advance.

---

## Shortlist Review Process

1. Operator locates the PASS run in `docs/research/robustness-sweep-matrix-v1.md`
2. Operator verifies all entry criteria above
3. Operator fills the candidate memo template
4. Operator adds the config to `docs/research/shortlist.csv`
5. Operator updates `Decision` in `docs/research/config-decision-matrix.md` to `PASS`
6. A separate explicit decision is required to promote from shortlist to `baseline_candidate`

---

## Candidate Memo Template

One memo per candidate config. File: `docs/research/candidate-memos/<config_id>-memo.md`

```markdown
# Candidate Memo — <Config ID>

## Config
- Config ID: <C001 / C002 / …>
- Config File: <yaml filename>
- Hypothesis ID: <H001 / H002 / …>
- Run ID: <run_id>
- config_hash: <hash>

## Robustness Verdict
- Status: pass
- Positive OOS splits: <n> / <total>
- Avg OOS Sharpe: <value>
- Worst OOS split return: <value>
- Total OOS trades: <n>

## Benchmark Comparison
- B01 (no_trade): outperform / underperform (with justification if underperform)
- B02 (HODL): outperform / underperform (with justification if underperform)
- B03 (simple baseline): outperform / underperform (with justification if underperform)
- B04 (previous baseline): outperform / n/a

## Hypothesis Clarity
- Hypothesis ID: <H001 / …>
- Hypothesis claim: <one sentence from hypothesis-registry.md>
- Does this result support the claim? <yes / partially / no — explain>

## Reproducibility
- Was the run reproducible from the config file alone? <yes / no>
- Any manual intervention required? <none / describe>

## Operator Decision
- Shortlist: <yes / no>
- Justification: <one or two sentences>
- Blockers (if not shortlisted): <describe>
```

---

## Shortlist Registry

File: `docs/research/shortlist.csv`

```csv
config_id,hypothesis_id,config_file,run_id,config_hash,verdict,shortlist_date,operator_decision,notes
```

Initial state (empty — no entries until a config passes all gates):

```csv
config_id,hypothesis_id,config_file,run_id,config_hash,verdict,shortlist_date,operator_decision,notes
```

---

## What Shortlist Does NOT Mean

- A shortlisted config is **not** a baseline candidate yet.
- A baseline candidate requires a separate explicit operator decision (see #636).
- Shortlist does not authorize paper execution.
- Shortlist does not authorize broker submission.
- Multiple configs may be shortlisted; only one may be declared baseline candidate at a time.

---

## Blockers That Prevent Shortlist

| Blocker | Resolution |
|---------|-----------|
| `Benchmark = blocked` | Address benchmark failure or provide documented justification |
| `config_hash` missing | Record hash before the confirmatory run (cannot be retroactive) |
| OOS redefinition detected | Disqualified; new config ID required |
| No candidate memo | Fill memo template before advancing |
| `robustness_verdict.json` missing | Run must complete and produce artifact |
