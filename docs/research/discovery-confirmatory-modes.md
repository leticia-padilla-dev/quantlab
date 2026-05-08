# Discovery and Confirmatory Validation Modes

## Purpose

OOS contamination happens when a researcher iterates on config parameters
after seeing OOS results. This document defines two distinct research modes
to prevent that contamination from invalidating the evidence.

---

## Two Modes

### discovery

| Property | Value |
|----------|-------|
| purpose | Learn patterns, detect hypotheses, explore parameter space |
| can_inform_variants | true |
| can_promote_directly | **false** |
| config_frozen | not required |
| oos_splits_locked | not required |
| contributes_to_candidate_review | **false** |

A discovery run generates learning. It may reveal which parameter regions
show promise. It may justify creating a controlled variant.

It cannot, on its own, support candidate review or shortlist promotion.

### confirmatory

| Property | Value |
|----------|-------|
| purpose | Validate a frozen config; produce promotion-eligible evidence |
| can_inform_variants | false — config is locked |
| can_promote_directly | false — still requires candidate shortlist review |
| config_frozen | **required** |
| config_hash_locked | **required** |
| oos_splits_locked | **required** |
| contributes_to_candidate_review | **true** |

A confirmatory run validates a specific, frozen config over locked OOS
splits. Its robustness verdict is the only verdict that may support
candidate review and shortlist promotion.

---

## When a Config Becomes Frozen

A config is frozen when:

1. The YAML file is finalized and committed with no uncommitted changes.
2. A `config_hash` is recorded in the config decision matrix.
3. The OOS split definitions are locked and will not change after this point.
4. The operator declares the run as confirmatory before execution begins.

A config that has been modified after seeing OOS results **cannot** be
treated as frozen. A new config ID is required.

---

## Config Hash

The `config_hash` is a stable identifier for a frozen config. It is derived
from the config file content and recorded in the config decision matrix
before confirmatory validation begins.

### Deriving config_hash

```bash
sha256sum configs/experiments/<config_file>.yaml | awk '{print $1}' | head -c 16
```

Record the result in the `config-decision-matrix.md` before the run starts.

### Rules

- `config_hash` must be recorded **before** the confirmatory run begins.
- If the config file changes after `config_hash` is recorded, the hash is
  invalid and the run result cannot be used for promotion.
- `config_hash` does not change between discovery and confirmatory for the
  same frozen config.

---

## OOS Redefinition Rule

OOS splits may not be redefined after a researcher has seen OOS results
for a given config.

Valid: defining splits before any run on a new config ID.
Invalid: changing split boundaries after observing that a particular split
was a catastrophic failure.

A researcher who needs different splits must use a new config ID and
document the reason.

---

## Decision Flow

```
researcher wants to validate a config
          │
          ├─ Is this a new exploration? ──► discovery mode
          │       │
          │       └─ run generates learning, may inform variants
          │           └─ cannot promote directly
          │
          └─ Is there a frozen config with locked OOS? ──► confirmatory mode
                  │
                  ├─ config_hash recorded before run? ──► No ──► BLOCKED
                  │
                  └─ Yes ──► run → robustness_verdict.json
                                └─ PASS → eligible for candidate shortlist review
                                └─ FAIL → classify cause → archive or controlled variant
```

---

## Integration with Config Decision Matrix

When updating `docs/research/config-decision-matrix.md`:

- Discovery runs do **not** update the `Verdict` column.
- Only confirmatory run results are recorded in `Verdict`.
- `config_hash` must appear in the matrix before `Verdict` is set.

---

## What This Does NOT Change

- The robustness gate thresholds remain unchanged.
- A confirmatory PASS still requires benchmark comparison before shortlist.
- Shortlist still requires candidate memo and operator decision.
- No config transitions to `baseline_candidate` without explicit operator decision.
- Paper execution remains blocked until baseline candidate is declared.
