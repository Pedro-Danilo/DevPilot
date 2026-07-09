---
doc_id: "POST-H-029-D-RELEASE-CANDIDATE-PROFILE-REPORT"
title: "POST-H-029-D — Release candidate test profile report"
status: "approved"
owner: "Ordonez"
created: "2026-07-09"
version: "1.0.0"
updated: "2026-07-09"
approval: "approved"
sprint: "POST-H-029-D"
source_of_truth: true
---
# POST-H-029-D — Release candidate test profile report

## Decision

`PASS` as implemented-initial/local-first.

POST-H-029-D adds a formal `release-candidate-local` test profile for operator-facing local RC verification. The profile is stored in `.devpilot/testing/release_candidate_test_profile.json` and validated by `src/devpilot_core/testing/release_candidate_profile.py`.

## Scope

The profile groups required, recommended and optional local commands covering:

- project state;
- docs governance;
- schema catalog;
- TCR v1/v2;
- test profile taxonomy;
- test impact rules;
- hardening quality gate;
- production-ready-local final declaration;
- UI/API local hardening;
- release candidate final report;
- source ZIP policy, artifact manifest and upgrade/rollback dry-run;
- P0/P1 pytest targets across POST-H-025/026/027/028/029.

## Safety

- Tests are not executed from JSON.
- Commands are data until an operator explicitly runs them.
- Network, external API, remote execution, connector write and plugin execution remain disabled.
- Shell arbitrary execution is blocked.
- `tests.run` remains approval-gated.

## Limitations

This is a first formal local release-candidate test profile. It does not replace full regression. It makes full-regression escalation explicit through `full_regression_required_when`; POST-H-029-E will add a historical regression guard for backlog and release closure decisions.
