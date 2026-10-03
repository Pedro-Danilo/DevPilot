---
doc_id: "DEVPL-GSDLC-13-D-03-JOB-RUNTIME-ADJUDICATION"
title: "13-D-03 RUN_01 second-attempt adjudication — validation job runtime and resumability"
status: "BLOCK / FUNCTIONAL-UX / ACTIVE-CORRECTIVE-PROJECTED"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-03"
approval: "projected_for_owner_windows_validation"
---

# 13-D-03 RUN_01 second-attempt adjudication

## Evidence reviewed

The second attempt reused the Windows-promoted repo461 corrective. Evidence shows the bounded successor StoryTestPlan with one required project-local test target, three residual unknown source paths, Owner review, APPROVE and Story transition to `VALIDATING`. It then planned typed `test` and `lint` jobs with Full Regression=0.

The attempt stopped at the first `test` execution. The captured Job Console shows the selected typed job still in `approved/planned`, progress `0%`, duration `0s`, no heartbeat and no execution logs/results. Returning to Story Code then renders `PENDIENTE / Sin StoryTestPlan todavía` and no planned jobs even though server-side runtime records had already been created.

The evidence set does not contain a raw authoritative start response proving lifecycle handoff. Therefore the correct adjudication is **BLOCK/indeterminate start**, not a claim that the test executed and failed.

## Root-cause findings

### `FUNC-13D03-JOB-LAUNCH-003` — S1

`StoryValidationJobApplicationService.start()` queued a job and spawned the worker with child stdout/stderr discarded, no explicit repo `src/` import path and no bounded launcher handshake. An early child startup/import failure could therefore terminate before `framework.start()` without being converted into governed evidence, leaving an unhelpful zero-progress state.

Corrective: preserve the fixed typed worker contract, add deterministic child import environment and a bounded handoff check. Early child exit while still queued becomes governed `error/BLOCK`; no arbitrary shell is added.

### `FUNC-13D03-RESUME-004` — S1

Story Code restored only SourceChangePlan state. `storyTestPlan` and `validationJobs` existed only in browser-view memory, so navigation/reconstruction lost their visible checkpoint despite persisted server runtime evidence.

Corrective: recover StoryTestPlan by current StoryExecution + exact current SourceChangePlan ID/hash and rehydrate its existing jobs when approved. Never use browser/session memory as authority.

### `UX-P1-13D03-004` — S2 absorbed

Direct navigation to `/jobs/{id}` inspected the selected job but did not load the job index, producing `0 registro(s)` next to a valid detail card. Active polling was also opt-in, so a running job could remain visually stale.

Corrective: load index+detail for direct links and automatically enable bounded polling only for active lifecycle states.

### `UX-P1-13D03-005` — S2 absorbed

After APPROVE the `Validar story` derivation action remained enabled. Server behavior was idempotent, so this was not an authority bypass, but the UX misleadingly suggested another validation action was required.

Corrective: once the current exact SourceChangePlan has a recovered StoryTestPlan, display it as current and disable re-derivation. A genuinely new SourceChangePlan naturally re-enables derivation.

## REVIEW_REQUIRED interpretation

`REVIEW_REQUIRED · unknown impact` is not a test failure and does not always appear. It appears only when current Test Impact/Test Contracts leave changed paths unexplained. For the Pilot A delta, the changed test artifact is an explainable required target while three source paths remain residual unknown.

The Owner reason is therefore a human governance statement about what residual unknown impact was reviewed and why proceeding with the bounded listed evidence is acceptable. It must not claim coverage DevPilot has not established. A valid example is: `Revisé los tres paths source aún no cubiertos por Test Contracts; acepto el riesgo residual para este micro-checkpoint y autorizo únicamente el test project-local requerido antes de Quality.`

## Validation scope

Corrective validation is focal/cumulative only: GSDLC-10-A/B/C, D13 bridge/governance, documentation governance, Source Registry schema, Story Code/10-A UI smoke and UI build. Full Regression remains exactly `0` under the 13-D sprint policy.

## PASS / BLOCK

PASS for this corrective requires focal tests/build/governance PASS, no forbidden archive content, and Windows evidence that current plan/jobs rehydrate and typed jobs have observable lifecycle handoff.

BLOCK if the corrective recreates/deletes runtime authority, introduces free-form shell/CWD, masks an early worker exit, rehydrates a stale plan from another SourceChangePlan, runs Full Regression, or advances to Quality without required terminal PASS evidence.

## Risk

Local/Linux validation can prove the real subprocess path and UI/build contracts but cannot substitute for Windows process-launch evidence. Windows validation remains mandatory before declaring this corrective promoted and resuming D03 Quality.

## Verification commands

Run the focal pytest set, docs governance validator, Source Registry schema validator, Story Code/10-A UI smoke and UI build. Do not invoke Full Regression for this intermediate checkpoint.
