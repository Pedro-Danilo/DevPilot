---
doc_id: "DEVPL-GSDLC-13-D-STORY-CODE-WORKBENCH-OPERATIONAL-CONTRACT"
title: "DEVPL GSDLC 13-D Story Code Workbench operational contract"
status: "approved"
version: "1.0.6"
owner: "Ordóñez"
updated: "2026-10-02"
approval: "projected_for_owner_windows_validation"
---

# 13-D Story Code Workbench operational contract v1.0.6

This revision supersedes v1.0.5 for the D02 continuation. It preserves all Draft/preimage/dry-run/approval/apply guarantees and adds server-authoritative SourceChangePlan resumability plus bounded progressive disclosure for the long Story Code surface.

## SourceChangePlan resumability

A persisted SourceChangePlan is runtime authority under `outputs/code_workbench/gsdlc_09_c/.../plans/`; browser `sessionStorage` is only a UX hint and must never be the only recovery pointer.

`GET /api/v1/story/code/status` projects `source_change_recovery` for the current StoryExecution. Recovery:

1. scans persisted immutable plans for the active workspace;
2. accepts only valid plan hashes bound to the current StoryExecution;
3. accepts only plans whose `draft_id` + `draft_revision_sha256` bindings still match the current Draft revisions in the Draft Set;
4. deterministically selects the latest exact current plan;
5. projects a persisted dry-run receipt only if its receipt hash, plan ID/hash and `source_mutations_performed=false` remain valid;
6. never mutates source while recovering.

A stale plan remains historical evidence but is not resurrected as the active plan. A tampered/unreadable plan is never selected.

Story Code must restore the active plan directly from this server projection even when no approval exists yet. Approval recovery is secondary and must filter approvals by the already recovered plan ID/hash rather than probing arbitrary historical approval subjects as plans.

## Restart semantics

After API/UI restart while Story remains `IN_PROGRESS`:

- Draft Set survives;
- per-Draft preimage state survives;
- current SourceChangePlan survives and is visible again;
- `Crear SourceChangePlan` remains disabled while the current exact plan is restored;
- Owner review confirmation resets to `PENDING` because it is a fresh human-session UI decision;
- plan recheck must be executed again before a new Dry-run when no persisted dry-run PASS exists;
- a valid persisted dry-run receipt may be rehydrated, but Owner review remains required before approval;
- final pre-apply recheck is never restored as authority and must be executed again after approval.

## Owner review gate

The Owner confirmation is a first-class gate, not a small incidental checkbox. The UI must expose a prominent full-width confirmation row and render the current sequence state near it.

When plan recheck passes but review is still pending, feedback must explicitly say:

`PASS · recheck vigente. Falta confirmar la revisión Owner para habilitar Dry-run.`

`Revalidar plan` remains enabled because drift detection is repeatable; its enabled state does not imply failure.

## Progressive disclosure

Story Code is a long multi-checkpoint surface. As a transitional UX hardening, top-level groups are collapsible:

- Story activation & context;
- Source tree + Draft editor;
- Agent assistance;
- Governed source change;
- Test Impact / StoryTestPlan;
- validation jobs;
- rollback;
- Git operations.

Rules:

- the section corresponding to current StoryExecution state opens by default;
- `Expandir todas` and `Colapsar inactivas` are available;
- expansion state is UI-only and may persist in `sessionStorage` by workspace + Story;
- a local BLOCK auto-expands its section and moves focus to the message;
- no security/approval state is stored as UI authority;
- action feedback remains local to the section that produced it.

## Existing D02 safety contract

The mandatory governed sequence remains:

`Draft Set → every Draft preimage PASS → immutable SourceChangePlan → Owner review confirmation → plan recheck → persisted dry-run PASS receipt → Owner approval request → Approval Center decision → final plan recheck → atomic apply`.

No terminal workaround, generic patch, Git stage/commit, external API, automatic approval or Full Regression is introduced.
