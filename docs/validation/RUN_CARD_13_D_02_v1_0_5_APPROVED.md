---
doc_id: "DEVPL-GSDLC-13-D-02-RUN-CARD"
title: "13-D-02 — Change Plan/apply — continuation after SourceChangePlan resumability corrective"
status: "approved"
version: "1.0.5"
owner: "Ordóñez"
updated: "2026-10-02"
approval: "projected_for_owner_execution"
checkpoint_id: "13-D-02"
continuation_run: "RUN_02"
---

# RUN CARD 13-D-02 v1.0.5

Continue the same preserved RUN_02 after promotion of the SourceChangePlan resumability corrective. Do not create another SourceChangePlan unless the persisted plan is explicitly reported stale/invalid by server authority.

## Entry state

- Story `story-rf-001 = IN_PROGRESS`;
- four runtime-only Drafts preserved;
- four per-Draft preimages PASS;
- persisted plan `source-plan-e4c37acd9038329150734b4c`;
- workspace source contains none of the four target files;
- no dry-run PASS receipt yet;
- no apply approval yet;
- Full Regression = 0.

## Restart/recovery validation

1. Authenticate as Owner with a fresh human session.
2. Open Story Code.
3. Confirm the server automatically restores `source-plan-e4c37acd9038329150734b4c` without pressing `Crear SourceChangePlan`.
4. Confirm the same four-path allowlist/full diff/risk/Test Impact are visible.
5. Confirm `Crear SourceChangePlan` is disabled while the restored current plan exists.
6. Confirm the active `Governed source change` section is expanded. Other top-level sections may be collapsed.
7. Confirm no historical-plan 403 probe storm occurs during normal restoration.

BLOCK if the plan is absent, a different plan is restored, source has mutated, or the UI asks the Owner to recreate the plan despite server recovery reporting it valid.

## Owner review → dry-run → approval → apply

8. Re-read allowlist, full diff, risk and Test Impact.
9. Mark the prominent Owner review confirmation. Require `REVIEW=CONFIRMED`.
10. Press `Revalidar plan`. Require `RECHECK=PASS`.
11. Press `Dry-run`. Require persisted PASS receipt + `source_mutations=false`.
12. Request Owner approval. Verify exact plan ID/hash/workspace/allowlist in Approval Center and approve only that artifact.
13. Return to Story Code and press `Revalidar plan` again. Require final recheck PASS.
14. Press `Aplicar plan aprobado` once.
15. Verify exact four changed paths, ApplyManifest, Story `CHANGES_READY`, no partial residue and no Git action.
16. STOP before D03.

## Required new evidence

Preserve all previous RUN_02 evidence. Add:

- `24_plan_rehydrated_after_restart.png`;
- `25_owner_review_confirmed_after_recovery.png`;
- `26_plan_recheck_pass_after_recovery.png`;
- `27_dry_run_receipt_pass.png`;
- `28_owner_approval_exact_plan.png`;
- `29_final_recheck_pass.png`;
- `30_apply_manifest_changes_ready.png`;
- `31_stop_before_d03.png`.

## PASS/BLOCK

PASS/PASS+FINDING only if the exact persisted plan is restored server-side without recreation, Owner review + recheck + dry-run + exact approval + final recheck + atomic apply complete in order, Story becomes CHANGES_READY, D03 remains untouched and Full Regression remains 0.
