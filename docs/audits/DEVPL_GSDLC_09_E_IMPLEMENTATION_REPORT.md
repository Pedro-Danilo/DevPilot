---
doc_id: "DEVPL-GSDLC-09-E-IMPLEMENTATION-REPORT"
title: "GSDLC-09-E — Story-level browser acceptance and one-full closure"
status: "implemented/local-qualified/windows-pending"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-08"
approval: "owner-approved-scope"
---

# GSDLC-09-E implementation report

## Scope
Closes Story/Coding Workbench by connecting approved atomic source apply to StoryExecutionState `IN_PROGRESS → CHANGES_READY` and surfacing the current story in Project Status. Browser Windows must demonstrate manual + agent-assisted paths, approved apply, rollback, external-edit conflict, Project Status coherence and negative authority guards.

## Architecture
- Existing 09-C remains the only source-write authority.
- Successful approved atomic apply advances an active StoryExecution runtime state to CHANGES_READY; blocked apply never advances state.
- Project Status remains read-only and now renders `planning.current_story`.
- Rollback remains approval-bound and exact-preimage; StoryExecution history is monotonic.
- 09-E consumes exactly one logical full through FRX-v2.4 current profile on Windows after all cheap gates/browser pass.

## Security
No generic shell, no force push, no agent self-apply/approve/commit, no runtime stores in packages. Source comparisons use semantic UTF-8 LF-normalized hashes.

## Maturity
This closes GSDLC-09 at an industrial local-first baseline. It is not a claim of distributed autonomous coding, remote orchestration, or production-scale multi-user concurrency; those remain future evolution.

## PASS/BLOCK
PASS when browser integrated journey is complete, Story reaches CHANGES_READY, rollback parity/conflict/negative guards pass, one governed full is 100% accounted with zero terminal FAIL/ERROR, S0/S1=0, and repo successor is clean. BLOCK otherwise.


## Corrective browser-00 — Project Status fallback + browser authority restoration

Windows browser evidence `GSDLC-09-E-00` exposed two pre-full issues. First, Project Status omitted the independent StoryExecution projection whenever WorkspaceEngineeringState legitimately fell back to UNKNOWN/EMPTY. The current-active service now attaches `current_story` after both success and fallback projection paths; it does not synthesize engineering-state PASS. Second, the Windows browser runner restores owner authority/session after the deliberate wrong-role negative case before collecting final parity evidence. Full Regression budget remains 0/1 and no FRX session is created by this corrective.

## Corrective browser-01 — Project Status UI source reconciliation

Windows browser evidence `GSDLC-09-E-01` confirmed that the backend StoryExecution projection and owner-session restoration were already corrected, but the visible Planning Journey panel still consumed `planningClosure().planning_closure` instead of the current StoryExecution projection returned by `projectStatus().project_status.planning.current_story`. The UI now merges the read-only `current_story` authority from Project Status into the Planning Journey view while preserving PlanningClosure as the authority for roadmap/backlog/sprint journey fields. No StoryExecution duplication or new mutation authority is introduced. The browser report is also hardened to record API StoryExecution readiness and UI Project Status readiness separately. Full Regression budget remains 0/1 and no FRX session has been created.
