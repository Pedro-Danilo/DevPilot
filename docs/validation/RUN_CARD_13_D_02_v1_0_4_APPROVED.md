---
doc_id: "DEVPL-GSDLC-13-D-02-RUN-CARD"
title: "13-D-02 — Change Plan/apply — continuation after Draft/plan governance corrective"
status: "approved"
version: "1.0.4"
owner: "Ordóñez"
updated: "2026-10-02"
approval: "projected_for_owner_execution"
checkpoint_id: "13-D-02"
continuation_run: "RUN_02"
---

# RUN CARD 13-D-02 v1.0.4

Continue the same preserved RUN_02 after promotion of the Draft/plan governance corrective. Do not delete the existing Draft Set or historical SourceChangePlan and do not create RUN_03.

## Entry state

- Story `story-rf-001 = IN_PROGRESS`;
- four runtime-only Drafts already exist;
- workspace source still contains none of the four target source/test files;
- historical plan `source-plan-69339fa58e713549ba5ecbc6` may remain as evidence;
- Full Regression = 0.

## Browser continuation

1. Authenticate as Owner immediately before continuing.
2. Open Story Code and confirm four Draft nodes.
3. Select each Draft. Confirm its own preimage state is shown; prior-file PASS must not carry over.
4. For each Draft press `Revalidar preimage`; require four independent PASS states.
5. Confirm `Guardar cambios en draft` is disabled when the selected Draft is unchanged. If you intentionally edit content, Save persists that runtime Draft revision and resets its preimage to PENDING; revalidate it again.
6. Create one **fresh** SourceChangePlan from the four current Draft revisions. The old historical plan is not deleted.
7. Review exact allowlist, full diff, risk and Test Impact. Confirm four intended paths only.
8. Interpret `unmatched_paths_total=4` as `REVIEW / unknown impact for D03`, not as test coverage PASS.
9. Mark the explicit Owner review confirmation.
10. Press `Revalidar plan`; require PASS.
11. Press `Dry-run`; require a persisted PASS receipt and `source_mutations=false`.
12. Only after dry-run PASS may `Solicitar approval owner` become enabled.
13. Request approval and open the directed Approval Center. Verify exact plan ID/hash, Owner role, workspace and allowlist; approve only that artifact.
14. Return to Story Code and press `Revalidar plan` again; require final recheck PASS.
15. Only then may `Aplicar plan aprobado` become enabled.
16. Apply exactly once. Verify exact four paths, ApplyManifest, Story `CHANGES_READY`, no partial residue and no Git action.
17. STOP before D03. Do not press `Validar story`.

## Required evidence additions

Preserve screenshots 01..15. Add:

- `16a_draft_preimage_domain.png`;
- `16b_draft_preimage_application.png`;
- `16c_draft_preimage_infrastructure.png`;
- `16d_draft_preimage_test.png`;
- `17_fresh_source_change_plan_owner_review.png`;
- `18_plan_recheck_pass.png`;
- `19_dry_run_receipt_pass.png`;
- `20_owner_approval_exact_plan.png`;
- `21_final_recheck_pass.png`;
- `22_apply_manifest_changes_ready.png`;
- `23_stop_before_d03.png`.

## PASS/BLOCK

PASS/PASS+FINDING only if four per-Draft preimages are independently PASS, Owner review is explicit, dry-run receipt exists before approval request, final recheck passes, atomic apply writes exactly the four allowlisted files, Story becomes CHANGES_READY, D03 is not started and Full Regression remains 0.

BLOCK if any toolbar/read-only state is misleading, any Draft preimage cannot be independently adjudicated, approval can be requested before dry-run, Test Impact/allowlist/diff cannot be understood, session expires without local recovery feedback, or apply mutates unexpected paths.
