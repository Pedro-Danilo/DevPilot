---
doc_id: "DEVPL-GSDLC-13-D-02-SOURCE-CHANGE-PLAN-RESUMABILITY-ADJUDICATION"
title: "13-D-02 — SourceChangePlan resumability after API/UI restart"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-02"
approval: "corrective-required"
---

# 13-D-02 — SourceChangePlan resumability adjudication

## Evidence

`CONT_05` resume-preflight returned PASS on repo459 and explicitly found:

- Story `story-rf-001 / IN_PROGRESS`;
- 4 Drafts preserved;
- 4 Draft preimages PASS;
- plan `source-plan-e4c37acd9038329150734b4c` persisted;
- source targets present = 0;
- persisted dry-run PASS receipt = false;
- Full Regression = 0.

After API/UI restart, Story Code showed the Drafts and their preimage states but did not show the persisted SourceChangePlan. `Crear SourceChangePlan` was enabled again.

API startup loaded Story Code status/drafts/sources and approvals, then attempted repeated GETs for historical approval subjects that returned 403. It did not retrieve the current pre-approval plan.

## Root cause

Repo459 `restoreApplyContext()` could discover a SourceChangePlan only from:

1. a browser `sessionStorage` pointer; or
2. an Approval Center record whose subject was a plan ID.

The current plan existed before dry-run/approval and therefore had no approval record. A restart/new browser session removed the sessionStorage pointer. The persistent runtime plan was consequently invisible to the UI despite remaining valid on disk.

## Classification

`FUNC-RESUME-13D02-SOURCE-PLAN-019 = S1 / ACTIVE-CORRECTIVE`.

This violates DevPilot resumability: a governed immutable artifact already persisted by DevPilot cannot require recreation merely because API/UI restarted.

## Corrective

- project current SourceChangePlan through server-authoritative Story Code status;
- filter by current StoryExecution + exact current Draft revisions + valid plan hash;
- project exact persisted dry-run receipt when valid;
- rehydrate UI directly from server status;
- never create a second plan just to recover UI state;
- stop historical approval-subject plan probes;
- keep Owner review and final recheck as fresh human-session gates.

## UX findings absorbed

The same corrective absorbs:

- `UX-P1-13D02-016`: prominent Owner review gate;
- `UX-P1-13D02-017`: explicit unmet prerequisite feedback;
- `UX-P1-13D02-018`: collapsible top-level Story Code sections.

## State preservation

Do not delete or recreate `source-plan-e4c37acd9038329150734b4c`. Preserve the same RUN_02, StoryExecution, Draft Set and evidence history. The corrective must restore this exact plan after promotion.
