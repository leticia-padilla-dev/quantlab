# De-Stepbit Migration Inventory

Issue: [#840](https://github.com/leticia-padilla-dev/quantlab/issues/840)
Epic: [#839](https://github.com/leticia-padilla-dev/quantlab/issues/839)

Status: Slice 1 inventory, Slice 2 Desktop removal, Slice 3 Research UI removal,
and Slice 4 external-consumer contract generalization completion records.
Historical documentation, public landing references, and the final audit remain
assigned to later slices.

## Canonical Decision

```yaml
canonical_decision:
  initiative: de_stepbit_quantlab
  stepbit_active_architecture: false
  stepbit_active_roadmap: false
  stepbit_active_runtime_dependency: false
  stepbit_future_delivery_commitment: false
  git_history_cleanup_required: false
```

QuantLab must be described as an operator-governed local research and
supervised execution system:

```text
Signals / hypotheses
        ↓
Human operator
        ↓
AI-assisted analysis and planning
        ↓
Local Python workflows
        ↓
QuantLab Core
        ↓
Execution safety boundary
        ↓
Canonical artifacts and evidence
        ↓
Human review
```

Authority model:

```yaml
authority:
  quantlab_core:
    - quantitative_validation
    - execution_engine
    - evidence_generation

  operator:
    - critical_approval
    - risk_limits
    - promotion_authority
    - live_authorization

  ai_assistance:
    - analysis
    - planning
    - code_assistance
    - explanation
    - no_execution_authority

  orchestration:
    current:
      - Python_workflows
    future_options:
      - optional_maintained_orchestration_tool
    mandatory_dependency: false
```

## Migration Success Metric

Do not measure this migration as `grep Stepbit == 0`.

Measure it as:

```yaml
migration_success:
  active_product_reference: 0
  active_runtime_dependency: 0
  active_roadmap_commitment: 0
  visible_user_surface: 0
  unexplained_transitional_identifier: 0
```

## Slice 1 Actions Taken

```yaml
updated:
  - README.md
  - .agents/current-state.md
  - docs/current-state.md
  - docs/roadmap.md
  - docs/architecture/quantlab-system-governance-matrix.md
  - docs/architecture/de-stepbit-migration-inventory.md

not_touched:
  - desktop runtime code
  - research_ui runtime code
  - CLI flags
  - IPC channel names
  - service identifiers
  - serialized fields
  - tests
  - contract files
```

## Slice 2 Desktop Actions Taken

```yaml
desktop_slice:
  issue: 842
  pr: 843
  merge_commit: 127c48228466e8f4914a431f5f48d96438828ce4
  status: completed

  removed:
    - visible_workspace_surfaces
    - assistant_adapter
    - preload_bridge_API
    - IPC_channel
    - IPC_handler
    - stepbit_service
    - STEPBIT_configuration
    - runtime_status_fields
    - renderer_actions_and_copy

  residual_stepbit_identifiers_in_desktop: []

  validation:
    typecheck: pass
    build: pass
    smoke_fallback: pass
    smoke_real_path: pass
    CI: pass
    reference_search: zero_matches

  tests:
    modified: false
    justification: "Existing Desktop typecheck, build, fallback smoke, and real-path smoke exercised the affected startup, preload, IPC, and renderer paths."
```

Slice 2 deliberately did not edit `research_ui`, CLI contracts, Python code,
or Python tests. Those remain assigned to later slices.

## Slice 3 Research UI Actions Taken

```yaml
research_ui_slice:
  issue: 846
  pr: 847
  status: completed

  removed:
    - visible_workspace_controls
    - frontend_state_and_fetches
    - workspace_state_cards
    - start_buttons_and_open_links
    - /api/stepbit-workspace
    - /api/stepbit-workspace/start
    - server_workspace_payload_builder
    - server_start_helper
    - start_state_and_live_url_detection
    - research_ui_stepbit_tests
    - research_ui_stepbit_readme_copy

  residual_stepbit_identifiers_in_research_ui: []

  validation:
    targeted_research_ui_tests: pass
    server_compile: pass
    startup_smoke: pass
    reference_search: zero_matches
```

Slice 3 deliberately did not edit Desktop, Core, CLI/json-request contracts,
or provider compatibility contracts. Those remain assigned to later slices.

## Slice 5 Actions Completed

```yaml
slice_5:
  issue: 850
  pr: 851
  status: completed

  canonical_docs_preserved:
    - docs/external-consumer-io-v1.md
    - docs/external-consumer-local-invocation-contract.md

  generalized_active_docs:
    - docs/advantages-and-future.md
    - docs/use-cases.md

  marked_historical:
    - docs/stepbit-io-v1.md
    - docs/stepbit-local-invocation-contract.md
    - docs/quantlab-stepbit-boundaries.md
    - docs/stepbit-integration.md

  marked_superseded:
    - docs/stepbit-io-v1.md
    - docs/stepbit-local-invocation-contract.md

  archived_or_moved: []

  active_navigation_removed: []

  negative_references_preserved:
    - docs/ops/stage-e-broker-live-scoping-prerequisites.md
    - docs/ops/stage-e-broker-live-prerequisite-gap-review.md
    - docs/ops/signed-action-roundtrip-validation.md
    - docs/ops/broker-no-submit-evidence-review.md
    - docs/ops/broker-reconciliation-evidence-pack.md
    - docs/ops/paper-live-repeatability-reaudit-after-session-03.md
    - docs/ops/supervised-paper-live-operating-cadence.md
    - docs/ops/supervised-paper-readiness-audit.md

  deferred:
    - path: landing/index.html
      reason: public landing page references, deferred to a separate web follow-up
      owner: web
      deferred_to: separate_web_follow_up
    - path: .agents/**
      reason: historical agent task files, preserved for audit trail
      owner: agents
      deferred_to: final_audit_or_dedicated_technical_follow_up

  technical_compatibility_identifiers:
    - identifier: test/test_stepbit_external_provider_compat.py
      classification: technical_compatibility_identifier
      reason: "Compatibility test intentionally preserved; outside the docs-only scope of Slice 5."
      owner: tests
      deferred_to: final_audit_or_dedicated_technical_follow_up

  retained_historical_stepbit_docs:
    - identifier: docs/stepbit-io-v1.md
      classification: intentional_historical_reference
      status: resolved_in_slice_5
    - identifier: docs/stepbit-local-invocation-contract.md
      classification: intentional_historical_reference
      status: resolved_in_slice_5
    - identifier: docs/quantlab-stepbit-boundaries.md
      classification: intentional_historical_reference
      status: resolved_in_slice_5
    - identifier: docs/stepbit-integration.md
      classification: intentional_historical_reference
      status: resolved_in_slice_5

  residual_stepbit_identifiers:
    - identifier: docs/architecture/de-stepbit-migration-inventory.md references to "stepbit"
      reason: inventory file explicitly documenting the migration, contains intentional references to stepbit for inventory purposes only
      owner: inventory
      deferred_to: final_audit_or_dedicated_technical_follow_up
    - identifier: docs/json-request-contract-verification.md line 11
      reason: historical evidence note, preserved as-is for audit trail
      owner: docs
      deferred_to: final_audit_or_dedicated_technical_follow_up

  classified_documents:
    - path: docs/advantages-and-future.md
      classification: active_canonical
      action: generalize_active_wording
      reason: "Active guidance generalized from former Stepbit-specific model; historical block replaced with active status line."
    - path: docs/use-cases.md
      classification: active_canonical
      action: generalize_active_wording
      reason: "Active use-case guidance; status line added, no Stepbit-specific wording in body."
    - path: docs/brand-guidelines.md
      classification: active_but_stale
      action: generalize_active_wording
      reason: "Binding source of truth; sections 9 and 10 contained active normative Stepbit product claims, generalized to external integrations."
    - path: docs/desktop-target-architecture.md
      classification: active_canonical
      action: generalize_active_wording
      reason: "Active ADR; three normative Stepbit claims removed or generalized to external consumer language."
    - path: docs/research-ui-product-direction.md
      classification: active_canonical
      action: generalize_active_wording
      reason: "Active product direction; two Stepbit product-surface claims removed."
    - path: docs/frontend-integration.md
      classification: obsolete_integration_plan
      action: mark_historical
      reason: "Describes former Stepbit-specific frontend integration model, superseded by external-consumer-io-v1.md."
    - path: docs/quantlab-desktop-v1.md
      classification: historical_evidence
      action: mark_historical
      reason: "Draft 2026-03-27 planning document describing Stepbit-inclusive desktop architecture, superseded by actual Desktop ADR and convergence work."
    - path: docs/desktop-v0.1-april-sprint.md
      classification: historical_evidence
      action: preserve_unchanged
      reason: "Sprint freeze scope document; Stepbit references are dated negative/out-of-scope items and do not imply current architecture."
    - path: docs/desktop-platform-convergence-status.md
      classification: historical_evidence
      action: preserve_unchanged
      reason: "Factual convergence completion record; all Stepbit references are dated traceability records of ported files and source snapshots."
    - path: docs/desktop-platform-convergence-inventory.md
      classification: historical_evidence
      action: preserve_unchanged
      reason: "Factual inventory of source snapshot; all Stepbit references are dated traceability hashes and source repository records."
    - path: docs/desktop-package-lock-policy.md
      classification: historical_evidence
      action: preserve_unchanged
      reason: "Policy decision document; Stepbit references are dated source repository traceability only."
    - path: docs/desktop-candidates-shortlist-v1.md
      classification: active_but_stale
      action: preserve_unchanged
      reason: "Plan-only document for a QuantLab Desktop feature; sole Stepbit reference is a negative out-of-scope item."
    - path: docs/workflow-operativo-codex.md
      classification: active_canonical
      action: generalize_active_wording
      reason: "Active governance document; sections 5, 6, and Reglas rapidas contained Stepbit-specific normative rules, generalized to external consumer/integration language."
    - path: docs/v0.1-evidence.md
      classification: historical_evidence
      action: mark_historical
      reason: "Release evidence record for v0.1 April 2026; Stepbit boundary status reference is an accurate historical evidence record, now marked with historical notice."
```

## Remaining Reference Classes

### 1. Desktop Runtime And UI

```yaml
classification: removed
risk: closed_for_desktop
reason: "PR #843 removed Desktop-side visible surfaces, bridge/API, IPC, service, config, and renderer copy."
issue: 842
pr: 843
residual_identifiers: []
validated_by:
  - "cd desktop && npm run typecheck"
  - "cd desktop && npm run build"
  - "cd desktop && npm run smoke:fallback"
  - "cd desktop && npm run smoke:real-path"
  - "rg Stepbit/stepbit patterns under desktop returned zero matches"
follow_up:
  status: complete
  note: "No Desktop-specific follow-up remains in this inventory."
```

### 2. Research UI Runtime And Controls

```yaml
classification: removed
risk: closed_for_research_ui
reason: "Slice 3 removed Research UI visible controls, frontend state, fetches, endpoints, start helpers, and targeted tests."
files:
  - research_ui/server.py
  - research_ui/app.js
  - research_ui/index.html
  - research_ui/styles.css
  - research_ui/README.md
  - test/test_research_ui_server.py
issue: 846
residual_identifiers: []
validated_by:
  - "python -m py_compile research_ui/server.py"
  - "python -m pytest -q test/test_research_ui_server.py"
  - "Research UI startup smoke"
  - "rg Stepbit/stepbit patterns under research_ui and test/test_research_ui_server.py returned zero matches"
follow_up:
  status: complete
  note: "No Research UI-specific follow-up remains in this inventory."
```

### 3. Contracts, CLI Examples, And Compatibility Fixtures

```yaml
classification: generalized
risk: closed_for_active_contracts
reason: "Slice 4 introduced canonical external-consumer contracts and preserved explicitly classified compatibility references."
issue: 848
pr: 849
canonical_files:
  - docs/external-consumer-io-v1.md
  - docs/external-consumer-local-invocation-contract.md
  - test/test_external_consumer_compat.py
compatibility_preserved:
  - docs/stepbit-io-v1.md
  - docs/stepbit-local-invocation-contract.md
  - test/test_stepbit_external_provider_compat.py
follow_up:
  status: complete
  note: "Historical Stepbit documents remain assigned to Slice 5; no active contract-generalization work remains."
```

### 4. Active Or Semi-Active Documentation To Reclassify

```yaml
classification: archive_or_generalize
risk: low_to_medium
reason: "Docs may still imply active product surfaces unless marked historical or generalized."
files:
  - docs/advantages-and-future.md
  - docs/use-cases.md
  - docs/brand-guidelines.md
  - docs/desktop-target-architecture.md
  - docs/research-ui-product-direction.md
  - docs/frontend-integration.md
  - docs/quantlab-desktop-v1.md
  - docs/desktop-v0.1-april-sprint.md
  - docs/desktop-platform-convergence-status.md
  - docs/desktop-platform-convergence-inventory.md
  - docs/desktop-package-lock-policy.md
  - docs/desktop-candidates-shortlist-v1.md
  - docs/workflow-operativo-codex.md
  - docs/v0.1-evidence.md
follow_up:
  issue_title: "docs: archive obsolete Stepbit integration material"
  required_action:
    - mark historical where retained
    - archive obsolete integration plans
    - remove from active navigation/roadmap
```

### 5. Operational Evidence Docs With Negative References

```yaml
classification: preserve_historical_or_negative_reference
risk: low
reason: "Many references explicitly record that no Stepbit work occurred or that Stepbit is forbidden."
examples:
  - docs/ops/stage-e-broker-live-scoping-prerequisites.md
  - docs/ops/stage-e-broker-live-prerequisite-gap-review.md
  - docs/ops/signed-action-roundtrip-validation.md
  - docs/ops/broker-no-submit-evidence-review.md
  - docs/ops/broker-reconciliation-evidence-pack.md
  - docs/ops/paper-live-repeatability-reaudit-after-session-03.md
  - docs/ops/supervised-paper-live-operating-cadence.md
  - docs/ops/supervised-paper-readiness-audit.md
follow_up:
  issue_title: "docs: archive obsolete Stepbit integration material"
  required_action:
    - preserve audit history where useful
    - do not rewrite historical evidence unless it implies active architecture
```

### 6. Landing / Public Page References

```yaml
classification: active_public_surface
risk: medium
reason: "Visible product copy should not present Stepbit as optional active product layer."
public_landing_follow_up:
  issue: 852
  status: in_progress
  path:
    - landing/index.html
  classification: active_public_surface
  action: remove_stepbit_public_copy
  final_audit: deferred
```

## Transitional Technical Identifiers Intentionally Preserved

These identifiers remain intentionally preserved after Slice 4 and are assigned
to Slice 5 or the final audit:

```yaml
identifiers:
  tests:
    - test_stepbit_external_provider_compat.py
  docs:
    - stepbit-io-v1.md
    - stepbit-local-invocation-contract.md
    - quantlab-stepbit-boundaries.md
```

Each transitional identifier requires a dedicated migration or deletion issue.
They must not be interpreted as current architecture.

## Next Slices

```yaml
next_slices:
  2:
    title: "desktop: remove Stepbit workspace surfaces"
    type: code_and_tests
    status: completed
    issue: 842
    pr: 843

  3:
    title: "research-ui: remove Stepbit workspace controls"
    type: code_and_tests
    status: completed
    issue: 846
    pr: 847

  4:
    title: "contracts: generalize Stepbit contracts for external consumers"
    type: docs_code_tests
    status: completed
    issue: 848
    pr: 849
    canonical_language: external_consumer_provider
    generalized:
      - New canonical docs: docs/external-consumer-io-v1.md and docs/external-consumer-local-invocation-contract.md
      - Updated CLI help text for --json-request to refer to external consumers instead of Stepbit
      - Updated docs/json-request-contract-verification.md to use external consumer terminology
      - Updated docs/cli.md examples to use outputs/external_demo instead of outputs/stepbit
      - Added new canonical test file: test/test_external_consumer_compat.py
    compatibility_aliases:
      - test/test_stepbit_external_provider_compat.py
      - docs/stepbit-io-v1.md
      - docs/stepbit-local-invocation-contract.md
    deprecated_identifiers:
      - No public identifiers deprecated yet; old stepbit-specific docs remain for compatibility (deferred to slice 5)
    deferred_to_slice_5:
      - docs/stepbit-io-v1.md
      - docs/stepbit-local-invocation-contract.md
      - docs/quantlab-stepbit-boundaries.md
      - docs/stepbit-integration.md
    residual_stepbit_identifiers:
      - identifier: test/test_stepbit_external_provider_compat.py
        reason: historical compatibility test file, preserved as alias for backwards compatibility
        owner: tests
        future_slice: 5
      - identifier: docs/stepbit-io-v1.md
        reason: historical documentation file, preserved temporarily for compatibility, deferred to slice 5 for archival
        owner: docs
        future_slice: 5
      - identifier: docs/stepbit-local-invocation-contract.md
        reason: historical documentation file, preserved temporarily for compatibility, deferred to slice5 for archival
        owner: docs
        future_slice: 5
      - identifier: docs/architecture/de-stepbit-migration-inventory.md references to "stepbit"
        reason: inventory file explicitly documenting the migration, contains intentional references to stepbit for inventory purposes only
        owner: inventory
        future_slice: final
      - identifier: docs/json-request-contract-verification.md line 11
        reason: historical evidence note, preserved as-is for audit trail
        owner: docs
        future_slice: 5

  5:
    title: "docs: archive obsolete Stepbit integration material"
    type: docs_only
    status: completed
    issue: 850
    pr: 851

  public_web_follow_up:
    title: "web: remove Stepbit from public landing copy"
    type: web_docs
    status: in_progress
    issue: 852
    path:
      - landing/index.html
    final_audit: deferred

  final:
    title: "audit: verify de-stepbit migration completion"
    type: audit
```

## Current Decision

```yaml
decision:
  stepbit_active_architecture: false
  stepbit_active_roadmap: false
  stepbit_runtime_references:
    desktop: removed
    research_ui: removed
  stepbit_contract_references:
    status: generalized
  stepbit_visible_surfaces:
    desktop: removed
    research_ui: removed
```
