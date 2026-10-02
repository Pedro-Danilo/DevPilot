---
doc_id: "DEVPL-GSDLC-13-D-STORY-CODE-WORKBENCH-OPERATIONAL-CONTRACT"
title: "DEVPL GSDLC 13-D Story Code Workbench operational contract"
status: "approved"
version: "1.0.5"
owner: "Ordóñez"
updated: "2026-10-02"
approval: "projected_for_owner_windows_validation"
---

# 13-D Story Code Workbench operational contract v1.0.5

This revision supersedes v1.0.4 for the D02 continuation. It preserves proposal v2.1, live-human-session fail-closed behavior and compact Source tree, and hardens Draft/preimage and Governed source change semantics after partial RUN_02 evidence.

## Draft semantics

`Aceptar propuesta → Draft Set` materializes the four reviewed proposal files as runtime-only SourceDraftBuffer records. It does not write workspace source.

`Guardar draft` is not required merely because ACCEPT created the Draft Set. Its role is to persist a **human edit** made in the Draft editor or to create/update an explicit manual Draft. In the UI it is presented as `Guardar cambios en draft` for an existing Draft and remains disabled while the editor matches the persisted Draft revision.

Each Draft owns an independent per-Draft `preimage_check` state:

- `PENDING` after materialization/save;
- `PASS` only after that exact Draft is revalidated;
- `CONFLICT` if source/target drift invalidates the preimage.

Selecting another Draft must show that Draft's own preimage state; PASS from another file must never be reused as a global message.

## SourceChangePlan Owner role

The Owner is not a button pusher. Before approval the Owner must review and affirm:

1. exact path allowlist;
2. full diff for every changed path;
3. risk and reasons;
4. Test Impact preview, including unmatched/unknown paths;
5. that the plan still represents the intended Story.

The UI exposes this as an explicit review confirmation bound to the current plan.

## Mandatory sequence

The governed sequence is:

`Draft Set → every Draft preimage PASS → immutable SourceChangePlan → Owner review confirmation → plan recheck → persisted dry-run PASS receipt → Owner approval request → Approval Center decision → final plan recheck → atomic apply`.

UI controls are progressively enabled by this sequence. Server authority additionally requires a persisted dry-run PASS receipt before an apply approval may be requested. This closes the former gap where approval could be requested directly after plan creation.

## Dry-run receipt

Dry-run persists a runtime-only receipt under the workspace outputs authority. The receipt binds plan ID/hash, StoryExecution, allowlist, risk, Test Impact, actor and `source_mutations_performed=false`. Approval request fails closed if the receipt is absent, stale, tampered or bound to another plan/hash.

## Test Impact interpretation

`test_impact_preview.status=PASS` means the analyzer completed successfully; it does **not** mean every path is covered by a Test Contract. If `unmatched_paths_total > 0`, Story Code must label this as `REVIEW` and state that D03 will classify unknown impact and derive the StoryTestPlan.

## Persistence model

Proposal, Drafts, SourceChangePlan and dry-run receipts are not merely process memory:

- proposals: `outputs/story_implementation/gsdlc_13_d_02/...`;
- Drafts: `outputs/code_workbench/gsdlc_09_b/.../drafts/`;
- SourceChangePlans: `outputs/code_workbench/gsdlc_09_c/.../plans/`;
- dry-run receipts: `outputs/code_workbench/gsdlc_09_c/.../dry_runs/`.

Workspace `src/` and `tests/` remain unchanged until approved atomic apply.

## Safety

No terminal workaround, direct filesystem write, generic patch, Git stage/commit or Full Regression is introduced. Human session, CSRF, RBAC, exact plan/hash approval, preimage protection and all-or-nothing apply remain fail-closed.
