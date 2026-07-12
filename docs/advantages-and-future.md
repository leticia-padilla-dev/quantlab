# Optional External AI Augmentation For QuantLab

Status: active guidance, generalized from the former Stepbit-specific model in Slice 5 (#850).

This document describes the value optional external AI tools can add to QuantLab without becoming its controlling authority.

The architectural rules are:

- External AI tools may amplify QuantLab
- External AI tools must not define QuantLab

## 1. Current Benefits Of Connecting Optional External AI Tools

### A. Reasoning-Assisted Analysis

External AI tools can help interpret QuantLab outputs:

- compare competing runs
- explain trade-offs between return, drawdown, and stability
- suggest follow-up experiments

Impact:

- faster research iteration without moving the research core out of QuantLab

### B. Workflow Assistance

External AI tools can automate auxiliary workflows around QuantLab:

- post-run analysis
- report interpretation
- recurring research routines
- human-in-the-loop workflow guidance

Impact:

- less manual glue work around the QuantLab core

### C. MCP-Based Access To Stable Artifacts

External AI tools can consume QuantLab's machine-facing surfaces:

- canonical artifacts
- `report.json.machine_contract`
- health and preflight surfaces
- run history outputs

Impact:

- cleaner external consumption without making QuantLab dependent on any single tool

## 2. What This Integration Should Not Become

External AI tools should not:

- own QuantLab's internal lifecycle
- own QuantLab's risk logic
- become the sovereign operator of QuantLab
- absorb QuantLab's trading authority

If those boundaries are crossed, the integration stops being optional and starts eroding QuantLab autonomy.

## 3. Future Improvements That Respect The Boundary

### A. Better External Analysis Flows

- richer AI interpretation of research artifacts
- comparison narratives over multiple runs
- structured strategy review workflows

### B. Cleaner Operator Interfaces

- dashboards over QuantLab outputs
- better visualization of paper sessions and live-safe telemetry
- guided execution review flows

### C. Reusable AI Workflow Templates

- post-run review templates
- paper-trading oversight workflows
- broker dry-run validation checklists

## 4. Boundary Rule For Future Work

Future integration work is good when it:

- improves the usefulness of QuantLab outputs
- improves operator understanding
- reduces friction at the external boundary

Future integration work is bad when it:

- makes QuantLab dependent on any single external tool to remain coherent
- relocates core authority away from QuantLab
- turns MCP into a total-control channel

## 5. Strategic Conclusion

The strongest future for QuantLab is:

- QuantLab continues to mature as an autonomous research, paper-trading, and future broker-execution system
- optional external AI and workflow augmentation layers remain available
- any integration stays contract-based, reversible, and non-invasive
