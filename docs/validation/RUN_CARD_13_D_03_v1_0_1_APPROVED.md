---
doc_id: "DEVPL-GSDLC-13-D-03-RUN-CARD"
title: "13-D-03 — Test Impact v2, StoryTestPlan, typed validation jobs and Quality Gate"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
approval: "owner-approved-for-corrective-retest"
updated: "2026-10-03"
authority: "successor-of-repo460-after-story-test-plan-targeting-corrective"
execution_mode: "OWNER-DRIVEN/DEVPL-EXECUTED/CHATGPT-ADJUDICATED"
full_regression_runs_allowed: 0
---

# RUN CARD 13-D-03 v1.0.1

## Purpose

Continue the **same RUN_01** after the first-attempt stop and demonstrate:

`Test Impact v2 → explainable StoryTestPlan → human review → typed targeted jobs → Quality Gate`.

No D02 operation is repeated. The original targetless StoryTestPlan remains historical evidence.

## Owner-facing process

1. `Validar story` derives/reviews a successor StoryTestPlan; it executes no tests.
2. Owner checks changed paths, required/recommended targets, unknown/sensitive impact and Full signal.
3. If `REVIEW_REQUIRED`, Owner writes a genuine review reason describing the residual unknown impact considered.
4. APPROVE authorizes the plan and transitions the Story to `VALIDATING`; it still executes no tests.
5. `Planificar jobs tipados` materializes allowlisted typed jobs from the approved plan.
6. Owner starts each required typed job and verifies terminal PASS evidence.
7. After required jobs PASS, `Abrir Quality Gate` takes the Owner to `Calidad / Tests`; Quality evaluates those fresh inputs. PASS transitions Story to `COMMIT_READY`.
8. STOP before D04/Git.

## Mandatory successor-plan expectations for Pilot A

The current D02 delta contains one exact changed test artifact. The successor StoryTestPlan must therefore show:

- required: `tests/test_create_product.py`;
- recommended: zero unless Test Impact v2 independently adds one;
- residual unknown: the three source paths;
- status: `REVIEW_REQUIRED`;
- sensitive impact: none;
- Full signal informational only;
- `execution_authorized=false` for Full Regression.

If no executable target exists, BLOCK. Do not approve or use terminal pytest.

## Owner decisions

### APPROVE

Accepts the validation plan for execution. Requires Owner role. When unknown impact exists, a human review reason is mandatory. APPROVE does not run tests.

### REJECT

Rejects the validation strategy and stops D03. Do not plan jobs from a rejected plan.

### WAIVER

Only applies to tests already classified `required` and explicitly `waivable=true`. It is Owner-only, reason-bound and temporary. It cannot waive sensitive/P0/unwaivable tests, cannot waive unknown impact and cannot create a missing target.

## Job rules

- no arbitrary shell;
- no free-form pytest command;
- project execution root is server-authoritative active workspace;
- `test` job uses StoryTestPlan targets;
- `lint` is typed/static and source-bounded;
- build only when applicable;
- Full Regression executions = 0.

## Quality rules

Quality PASS requires fresh required job evidence and zero blocking S0/S1. Remediation may prepare proposals/handoffs but never self-apply. PASS ends in `COMMIT_READY`; D04 remains untouched.
