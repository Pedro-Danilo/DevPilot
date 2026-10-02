---
doc_id: "DEVPL-GSDLC-13-D-02-RUN-CARD"
title: "Run Card 13-D-02 — Change Plan/apply continuation after session-feedback + compact-tree corrective"
status: "approved"
version: "1.0.3"
owner: "Ordóñez"
updated: "2026-10-02"
approval: "projected_for_owner_execution"
checkpoint_id: "13-D-02"
continuation_run: "RUN_02"
full_regression_runs_allowed: 0
---

# Purpose

Continue the same preserved RUN_02 after promotion of the session-feedback/compact-tree corrective. Proposal v2.1 becomes accepted-for-review but has not been converted to Draft Set. Do not reset StoryExecution, delete proposals, create a new RUN number or bypass human authentication.

# Required start state

- successor DevPilot commit is HEAD==origin and worktree clean;
- `story-rf-001 = IN_PROGRESS`;
- historical deterministic v2 proposal remains persisted `PROPOSED` with `draft_ids=[]`; it is obsolete after this corrective and must not be ACCEPTed;
- source real files = 0;
- Draft Set = 0;
- screenshots 01..06 and the captured `99_block_state_v2.png` remain preserved;
- Full Regression=0.

# Browser continuation acceptance

1. Authenticate as Owner immediately before the continuation.
2. Open Story Code and verify the same Story is `IN_PROGRESS`.
3. Press `Proponer implementación desde contexto` once. This must create/recover the current deterministic v2.1 proposal. The historical v2 proposal remains evidence and must be rejected as obsolete if a decision is attempted.
4. Verify the proposal model is `deterministic-story-implementation-template-v2.1`, quality includes `json_serializable_type_contract=true`, and `Source tree` shows only file names as file rows; no `PROPOSAL ·` prefix is visible inside leaf labels.
5. Verify `Información y provenance` is collapsed by default; expand it once and confirm policy, proposal status, provider/model/profile/quality and provenance are still available; collapse it again.
6. Select and review all four v2.1 PROPOSAL files; Editor must be read-only and Draft toolbar hidden. Confirm `ProductAttributes` is JSON-compatible but still does not invent business fields.
7. Press `Aceptar propuesta → Draft Set` exactly once.
8. Verify exactly four DRAFT paths and `source_mutations=false`.
9. Revalidate preimage of all four Drafts.
10. Create one multi-file SourceChangePlan; review full diff, risk, Test Impact and exact allowlist.
11. Recheck plan; execute dry-run; source mutation must remain false.
12. Request exact Owner approval, decide it in Approval Center, return to Story Code and run the final recheck.
13. Apply exactly once; verify ApplyManifest, exact changed paths and Story `CHANGES_READY`.
14. STOP before D03.

# Local feedback acceptance

For proposal/Draft and SourceChange actions, PASS/BLOCK feedback must appear directly inside the active panel. A page-level status may mirror it but must not be the only message.

If the human session is invalid before a D02 mutation:

- action must fail closed before the governed mutation;
- the local panel must state that session is no longer valid and state is preserved;
- a reauthentication link returning to `/story/code` must be visible;
- do not use token fallback or terminal/API workaround.

During this retest, do not intentionally wait for session expiry merely to create a 401; static/focal tests cover the error rendering contract.

# BLOCK conditions

STOP without workaround if:

- current proposal is not v2.1 or an obsolete v2 proposal can still be ACCEPTed;
- ACCEPT produces anything other than four exact Drafts;
- source mutates before approved apply;
- leaf labels again contain state prefixes or button-style chrome;
- Source-tree information cannot be collapsed;
- Draft toolbar remains active during PROPOSAL read-only review;
- a D02 action returns 401 but the feedback is only visible at page top;
- exact plan/approval/hash/path binding fails;
- Story does not become `CHANGES_READY` after successful apply;
- Full Regression is invoked.
