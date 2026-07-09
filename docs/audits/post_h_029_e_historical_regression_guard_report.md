---
doc_id: "POST-H-029-E-HISTORICAL-REGRESSION-GUARD-REPORT"
title: "POST-H-029-E — Historical regression guard report"
status: "approved"
owner: "Ordonez"
created: "2026-07-09"
version: "1.0.0"
updated: "2026-07-09"
approval: "approved"
sprint: "POST-H-029-E"
source_of_truth: true
---
# POST-H-029-E — Historical regression guard report

## Decision

`PASS` as implemented-initial/local-first.

POST-H-029-E adds a schema-backed historical regression guard for DevPilot closure decisions. The guard is implemented in `src/devpilot_core/testing/historical_regression_guard.py` and exposed through `python -m devpilot_core tests regression-guard`.

## Scope

The guard formalizes whether a closure requires:

- full regression;
- expanded focal regression;
- a temporary waiver with owner, reason, risk, tests executed and expiration;
- or a pending/blocking state.

The first version is intentionally non-executing. It validates the regression decision, impact context and supporting POST-H-029 components without running `pytest -q` or storing heavy runtime logs in the repo.

## Closure behavior

- `micro-sprint` context allows expanded focal validation when no sensitive or unmapped change requires full regression.
- `backlog-closure`, `release-candidate` and `major-hito` contexts require an explicit decision.
- Undecided closure is blocked.
- Sensitive paths such as schema catalog, project_state, quality gate, CLI core, API security, production-ready claims and TCR schema require full regression or a valid waiver.
- Waivers are temporary and must expire.

## Quality gate

`testing-tiers-ready` is registered in hardening/industrial quality-gate profiles. It validates:

- TestProfileTaxonomy;
- TestImpactRuleRegistry;
- TCR v1/v2;
- ReleaseCandidateTestProfile;
- HistoricalRegressionGuardReport;
- local-first/no-network/no-external-API invariants.

## Safety

- `tests_executed=false` inside the guard.
- `network_used=false`.
- `external_api_used=false`.
- `source_mutations_performed=false`.
- Runtime validation logs remain evidence references, not source-controlled truth.

## Limitations

This is an implemented-initial closure guard. It does not execute tests and does not replace operator judgment. A future evolution may add stronger evidence ingestion from externally generated validation logs, but must keep runtime logs out of source archives.
