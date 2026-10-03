---
doc_id: "DEVPL-GSDLC-13-D-03-RUN-CARD"
title: "13-D-03 — Test Impact v2, StoryTestPlan, typed validation jobs and Quality Gate"
status: "approved"
version: "1.0.2"
owner: "Ordóñez"
approval: "projected-for-owner-windows-validation"
updated: "2026-10-03"
authority: "successor-of-repo461-after-job-runtime-resumability-corrective"
execution_mode: "OWNER-DRIVEN/DEVPL-EXECUTED/CHATGPT-ADJUDICATED"
full_regression_runs_allowed: 0
---

# RUN CARD 13-D-03 v1.0.2

## Purpose

Continue the **same RUN_01** after the first-attempt stop and demonstrate:

`Test Impact v2 → explainable StoryTestPlan → human review → typed targeted jobs → Quality Gate`.

No D02 operation is repeated. The original targetless StoryTestPlan remains historical evidence. The already approved successor StoryTestPlan and already planned validation jobs from the second attempt are also preserved; this revision resumes from them instead of recreating them.

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
## Resumption after second-attempt runtime defect

The second attempt already proved the successor StoryTestPlan review/APPROVE path and materialized typed `test` + `lint` jobs. It then stopped because the `test` start was not demonstrated as an observable lifecycle execution and Story Code lost the plan/jobs after navigation.

After promotion of the bounded runtime/resumability corrective:

1. keep the same `RUN_01`;
2. restart DevPilot API/UI, do not recreate D02 source changes;
3. Story Code must automatically rehydrate the same approved StoryTestPlan and existing job records;
4. capture the rehydrated validation panel before starting anything;
5. for each required current job:
   - terminal `pass`: preserve and do not rerun;
   - `planned`/`approved`: press `Iniciar` once;
   - `queued`/`running`: open Job Console and observe heartbeat/polling; do not start again;
   - `error`/stale: create at most the governed retry allowed by the existing retry budget, preserving the original record;
6. Job Console must show the selected job in the index/detail and observable lifecycle (`queued/running` or terminal) rather than an unexplained approved/0% snapshot after accepted start;
7. `test` and every other required typed job must end terminal PASS before Quality;
8. open Quality Gate and adjudicate fresh evidence; only Quality PASS may transition Story to `COMMIT_READY`;
9. STOP before D04/Git.

### Evidence required back

Return one evidence folder/ZIP containing at minimum:

- corrected repo authority HEAD and clean Git status;
- screenshot of Story Code after restart showing the recovered APPROVED StoryTestPlan and jobs;
- screenshot of Job Console for `test` showing observable lifecycle and then terminal result;
- screenshot/result for the remaining required typed job(s);
- sanitized job logs and structured result/JUnit refs;
- Quality Gate result and final Story state;
- transcript of the single continuation procedure;
- explicit `full_regression_runs=0`.

### Additional PASS/BLOCK

PASS requires route rehydration, observable worker handoff, all required jobs terminal PASS, fresh Quality PASS, Story=`COMMIT_READY`, and Full Regression=0.

BLOCK on disappeared current plan/jobs after navigation, worker launch that exits before lifecycle handoff, stale/error evidence left unresolved, Quality evaluated without fresh required job PASS, arbitrary shell/CWD input, or any Full Regression execution.

