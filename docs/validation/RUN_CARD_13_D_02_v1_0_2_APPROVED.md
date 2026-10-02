---
doc_id: "DEVPL-GSDLC-13-D-02-RUN-CARD"
title: "Run Card 13-D-02 — Change Plan/apply continuation after proposal quality + UX corrective"
status: "approved"
version: "1.0.2"
owner: "Ordóñez"
updated: "2026-10-01"
approval: "projected_for_owner_execution"
checkpoint_id: "13-D-02"
continuation_run: "RUN_02"
full_regression_runs_allowed: 0
---

# Purpose

Continue the same preserved `RUN_02` after Windows promotion of the proposal-quality/tree-review corrective. Do not reset StoryExecution, delete the v1 proposal or create a new RUN number.

# Required start state

- DevPilot successor commit promoted and HEAD==origin;
- `story-rf-001 = IN_PROGRESS`;
- v1 proposal remains historical `PROPOSED` but has `draft_ids=[]`;
- source tree real files = 0;
- Draft Set = 0;
- screenshots 01 and 02 from the partial RUN_02 remain preserved;
- Full Regression=0.

# Browser continuation

1. Start API/UI normally and open Story Code.
2. Confirm the separate `Implementación propuesta por DevPilot` panel no longer exists.
3. In `Source tree`, press `Proponer implementación desde contexto` once.
4. Verify proposal uses `deterministic-story-implementation-template-v2` and `quality=true`.
5. Capture `03_proposal_v2_tree_editor.png` showing the filesystem tree with `PROPOSAL` nodes.
6. Click every proposed file; verify each opens read-only in `Editor de draft` and contains Purpose/Responsibilities/Boundaries/Traceability docstring.
7. Confirm paths exactly:
   - `src/inventory_sales_local_greenfield/domain/product.py`;
   - `src/inventory_sales_local_greenfield/application/create_product.py`;
   - `src/inventory_sales_local_greenfield/infrastructure/sqlite_product_repository.py`;
   - `tests/test_create_product.py`.
8. Verify quality/provenance disclosure states: ARC-C02/C03/C04=true, story_specific_storage=false, reusable_product_storage=true, business_field_invention=false.
9. If review is coherent, press `Aceptar propuesta → Draft Set` exactly once.
10. Capture `04_draft_set_tree_editor.png`; same tree paths must now be `DRAFT`, editor editable, source mutations=false.
11. Revalidate preimage of every Draft.
12. Create one multi-file SourceChangePlan and continue the existing D02 sequence: plan review → recheck → dry-run → Owner approval → final recheck → atomic apply.
13. STOP before D03 with Story `CHANGES_READY`.

# BLOCK conditions

STOP without workaround if:

- UI still shows a separate proposal panel;
- proposal model is v1;
- any v1 proposal can still be accepted;
- tree does not expose all four proposal paths;
- a proposal file is editable before ACCEPT;
- any module lacks the required docstring sections;
- proposal uses story-specific storage/table naming;
- source or drafts mutate before ACCEPT;
- any path differs from proposal allowlist;
- Full Regression is invoked.
