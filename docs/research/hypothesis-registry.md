# Hypothesis Registry

Each research hypothesis has a unique ID, a clear claim, and a declared scope.
A hypothesis that is not registered may not be promoted.

## Registry

| Hypothesis ID | Claim | Asset Universe | Strategy Family | Status | Notes |
|---------------|-------|----------------|-----------------|--------|-------|
| H001 | RSI mean-reversion with cooldown generates positive risk-adjusted OOS returns on ETH during 2021–2024 | ETH | RSI cooldown | ACTIVE | First confirmatory candidate |
| H002 | RSI mean-reversion with cooldown generalizes to BTC during 2021–2024 | BTC | RSI cooldown | ACTIVE | Cross-asset generalization test |
| H003 | Simple momentum baseline provides a useful weak benchmark for RSI configs | BTC, ETH | Simple momentum | ACTIVE | Benchmark peer only |

## Rules

- Each hypothesis must have a unique ID (H001, H002, …).
- A hypothesis may map to multiple configs.
- A hypothesis may only be promoted to confirmatory validation if it passes robustness review.
- Discovery runs may reference a hypothesis but cannot promote it directly.
- A hypothesis that has been archived may not be re-opened without a new ID and documented reason.

## Decision States

| State | Meaning |
|-------|---------|
| ACTIVE | Under research or review |
| PASS | Robustness gate passed at least once |
| ARCHIVED | No further iteration warranted |
| PROMOTED | Moved to candidate shortlist |
