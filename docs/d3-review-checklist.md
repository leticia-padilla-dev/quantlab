# Pre-D.3 Review Checklist

## Purpose

Define the requirements that must be met before a D.3 micro-live review
can be considered. D.3 is not automatic. It requires explicit operator
decision with documented paper evidence.

This checklist is used after paper strategy trial level_3 completes.

---

## Trigger

This checklist applies only when:

- Paper strategy trial level_3 has completed all sessions
- No unresolved hard stops exist in the paper session record
- Operator notes are complete for all sessions

---

## Pre-D.3 Checklist

### Evidence Requirements

- [ ] Paper strategy trial level_3 completed (10+ sessions or 2+ weeks)
- [ ] All operator notes filed for every session
- [ ] No unresolved hard stops across level_3
- [ ] Reconciliation passed in all level_3 sessions
- [ ] Artifacts complete and recoverable for all level_3 sessions
- [ ] Behavior consistency confirmed across level_3 sessions

### Capital and Risk Limits

- [ ] Maximum capital exposure for micro-live defined in writing
- [ ] Daily loss limit defined in writing
- [ ] Per-session loss limit defined in writing
- [ ] Capital limits reviewed and approved before any micro-live consideration

### Alert and Artifact Requirements

- [ ] Alert artifact requirements defined (what triggers an alert, who receives it)
- [ ] Artifact path requirements confirmed for micro-live sessions
- [ ] Log recovery process confirmed

### Reconciliation Requirements

- [ ] Reconciliation process confirmed for live orders (not just simulated)
- [ ] Reconciliation discrepancy escalation path defined
- [ ] Broker order state vs. strategy state comparison process defined

### Stop-Control Checklist

- [ ] Hard stop conditions defined for micro-live (may differ from paper)
- [ ] Operator knows how to execute a hard stop in live context
- [ ] Emergency stop process tested in paper context

### Secret Boundary Checklist

- [ ] Private keys are not in any log file, artifact, or config file
- [ ] API credentials are not exposed in any output
- [ ] Signal file path does not expose sensitive information
- [ ] No credentials committed to the repository

---

## Capital Limits Template

Define before any D.3 consideration:

```
capital_limits:
  max_total_exposure_usd: <amount>
  daily_loss_limit_usd: <amount>
  per_session_loss_limit_usd: <amount>
  currency: USD
  review_date: <YYYY-MM-DD>
  approved_by: <operator>
```

---

## What D.3 Is NOT

- D.3 is not Stage E
- D.3 is not automated execution authorization
- D.3 is not a license to increase capital beyond defined limits
- Completing this checklist does not authorize broker submission

D.3 review eligibility means the operator may evaluate whether a micro-live
session is warranted. The decision to proceed with micro-live is separate
and requires explicit authorization.

---

## Stage E Remains Blocked

Stage E requires a decision entirely outside this checklist. No combination
of paper trial completion and D.3 review eligibility opens Stage E.
