---
doc_id: "DEVPL-GSDLC-13-D-STORY-CODE-WORKBENCH-OPERATIONAL-CONTRACT"
title: "DEVPL GSDLC 13-D Story Code Workbench operational contract"
status: "approved"
version: "1.0.7"
owner: "Ordóñez"
updated: "2026-10-03"
approval: "projected_for_owner_windows_validation"
---

# 13-D Story Code Workbench operational contract v1.0.7

This revision supersedes v1.0.6 for the D03 continuation. It preserves every D01/D02 activation, context, Draft, SourceChangePlan, dry-run, approval, apply and resumability guarantee and adds a bounded StoryTestPlan/validation execution contract for `13-D-03`.

## D03 mental model

D03 does not write source. Its purpose is to decide **what evidence must be executed for the already-applied Story change**, execute only typed/allowlisted local validation jobs, and evaluate Story Quality before Git is allowed.

The governed sequence is:

`CHANGES_READY → Test Impact v2 → StoryTestPlan human review → APPROVED → VALIDATING → typed jobs → Quality Gate → COMMIT_READY`.

`Validar story` derives a plan; it does not execute tests. `Aprobar StoryTestPlan` accepts that plan for governed execution; it also does not execute tests. Test execution starts only when an allowlisted typed validation job is explicitly started.

## StoryTestPlan targeting contract

Test Impact v2 remains the only Test Impact engine and remains authoritative for Test Contract/rule matching. D03 must not implement a second impact analyzer.

A changed file that is itself an exact project-local Python test artifact (`tests/**/*.py`) in the immutable SourceChangePlan is additionally a deterministic StoryTestPlan execution target when all of these conditions hold:

1. it is in the exact SourceChangePlan changed-path allowlist;
2. it resolves safely inside the server-authoritative active workspace;
3. it exists physically in that workspace;
4. it is under `tests/` and ends in `.py`.

This bounded rule does not infer coverage for unrelated source. It only states that a test artifact deliberately created/changed by the Story must run before that Story can be judged ready.

The reason is recorded as `source-change:changed-project-test-artifact`; its policy is non-waivable for the current StoryTestPlan.

## `REVIEW_REQUIRED`

`REVIEW_REQUIRED` is **not** a test failure. It means one or more changed paths remain outside the current Test Impact/Test Contract explanation and therefore require an authenticated human Owner review before approval.

The UI must show:

- changed paths;
- required tests and why each is required;
- recommended tests and why each is recommended;
- residual unknown impact;
- sensitive impact;
- Full signal as informational only;
- whether at least one executable target exists.

If unknown impact exists, approval requires a non-empty human review reason. If unknown impact exists and the effective required+recommended target set is empty, approval is server-side BLOCK even if a browser incorrectly enables a button.

## Owner decisions

### APPROVE

Owner APPROVE means: "I reviewed this StoryTestPlan, understand the residual unknown/sensitive impact, and authorize only the listed typed validation evidence to proceed."

APPROVE:

- requires authenticated human authority;
- transitions the Story toward `VALIDATING` through the existing application boundary;
- does not execute tests by itself;
- does not mutate source;
- cannot bypass targetless unknown impact.

### REJECT

REJECT means the Owner does not accept the proposed validation strategy. D03 stops. No typed validation jobs should be planned from a rejected StoryTestPlan.

### WAIVER

A waiver is **not** a generic override for unknown impact, a failing test, or missing targets. It is a time-bounded Owner exception for one or more tests that are already classified `required` **and** whose server-side policy explicitly marks them `waivable=true`.

Rules:

- Owner-only;
- reason mandatory;
- TTL 1..1440 minutes;
- sensitive-impact required tests cannot be waived;
- P0/unwaivable required tests cannot be waived;
- a waiver cannot create a missing test target;
- agent/model authority cannot waive.

The button must remain disabled when no current required test is waivable.

## Validation job execution-root contract

Typed validation jobs are planned by DevPilot, never by arbitrary shell text from the browser.

For a real active project workspace, the immutable job context must bind:

- `workspace_id`;
- an absolute `execution_root` resolved server-side from `UiWorkspaceContext`;
- `execution_root_source=server-active-workspace`;
- StoryTestPlan ID/hash;
- exact typed target set;
- bounded limits;
- `full_regression=false`.

The worker executes project tests/lint from this authoritative project execution root. It must reject an execution root that is missing, non-absolute, untrusted, not a directory, or whose `.devpilot/project.yaml` identity does not match the immutable workspace binding.

Runtime job metadata/evidence may remain under the DevPilot platform runtime root; project command CWD and project target resolution must use the bound active workspace root.

No browser-supplied CWD/path authority is accepted.

## Quality handoff

After typed jobs are planned, Story Code exposes `Abrir Quality Gate` as a navigational handoff to `/quality`. The link carries no quality authority and executes nothing; it only preserves the StoryTestPlan quality context needed by the existing Quality surface. The Owner must inspect fresh job results before evaluating Quality.

## D03 PASS boundary

D03 can advance to `COMMIT_READY` only when:

- StoryTestPlan is bound to the exact D02 SourceChangePlan;
- required/recommended targets are explainable;
- unknown/sensitive impact is explicit;
- Owner review is valid;
- Story is `VALIDATING` before job execution;
- typed jobs execute without arbitrary shell;
- required jobs finish PASS;
- Story Quality Gate returns PASS / `commit_ready=true`;
- Full Regression executions remain `0`;
- D04 Git has not started.

Remediation remains proposal/handoff-first and cannot self-apply source changes.
