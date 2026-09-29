---
doc_id: "DEVPL-GSDLC-13-C-04-C04-BR-107-IMPLEMENTATION-REPORT"
title: "C04_BR_107 — Guided next-action authority reconciliation corrective"
status: "POST_UI_PASS_PROMOTION_DEFERRED"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-29"
approval: "owner_reviewed_blocked_by_c04_br_108"
---
# C04_BR_107 — Guided next-action authority reconciliation

## Objective

Reconcile the persistent server-authoritative Guided SDLC header with the already-correct Planning closure state. C04_BR_106 proved Roadmap/Backlog/Sprint `FROZEN` and Planning `IMPLEMENTING_READY`, but `/guided-sdlc/status` still replaced its `next_action` with historical `PRE_CODE_READY_PLANNING_NEXT` whenever Pre-code remained READY.

## Root cause

Three historical projections were individually valid for earlier milestones but no longer mutually consistent:

1. `GuidedSDLCApplicationService` overlaid `PRE_CODE_READY_PLANNING_NEXT` solely from Pre-code readiness and did not consult Planning closure.
2. `PlanningClosureApplicationService` still projected `GSDLC_09_REQUIRED` / unavailable after `IMPLEMENTING_READY`, although GSDLC-09 and the Story Code Workbench are already implemented.
3. `PlanningAuthoringApplicationService` returned terminal `recommended_next=closure`, so the Planning notice exposed `siguiente: closure` rather than the executable successor surface.

## Implementation

- Planning closure now projects `IMPLEMENTING_READY_STORY_CONTEXT_NEXT`, `available=true`, target `ui.story-code-workbench`.
- Guided Project Status reads Planning closure as a read-only bounded overlay after Pre-code is READY. It preserves the formal global MIPSoftware phase/lifecycle projection and changes only the existing schema fields `current_step` and `next_action`.
- At `IMPLEMENTING_READY`, Guided `current_step` becomes `story-context-readiness` and next action points to Story Code Workbench. No ad-hoc `ProjectStatus` fields or progress keys are introduced.
- Planning Authoring terminal recommendation is `story-code` rather than `closure`.
- Planning Workbench uses the server closure label in its status notice and removes the pilot-specific `13-D-01` Run Card id from product copy.
- Project Status recognizes the `story-context-readiness` boundary as Build/Validate current rather than falling back to Pre-code.

## Authority and safety

No Planning JSON, Markdown projection, Pre-code source artifact, global MIPSoftware registry or workspace source is mutated by this reconciliation. It is a read-only authority composition fix. The global MIPSoftware lifecycle remains available through `current_step_global_mipsoftware`; C04_BR_107 does not claim that the formal global MIP phase was advanced.

## Frozen artifact revision finding

Planning already requires a successor semantic version after FROZEN. Generic artifact governance supports FROZEN/APPROVED hash drift -> `REVALIDATION_REQUIRED` -> DRAFT with version lineage, but the current Pre-code Wizard does not yet expose a general Owner-initiated successor-version workflow for all seven FROZEN Pre-code artifacts. This is recorded as a product-governance hardening gap; it is not implemented inside C04_BR_107 because it is broader than the current Planning next-action defect.

## Template completeness finding

Artifact profiles currently define **minimum** required/recommended headings, and the Pre-code catalog remains `implemented-initial`. They are validation profiles, not a universal guarantee that every professional project artifact contains every potentially relevant section. Future production hardening should evolve profiles toward required + recommended + conditional sections by project type/risk/architecture, while preserving deterministic validation.

## Markdown E2E classification

The six Markdown files in the current workspace remain migration/backfill evidence from C04_BR_105. Product lifecycle integration is proven automatically without reconcile, but browser-level fresh-journey creation evidence is still pending for a future clean Planning journey. That is an acceptance-evidence gap, not an unimplemented Markdown feature.

## PASS criteria

- global persistent header, Project Status and Planning guidance agree on the successor surface;
- `/guided-sdlc/status` next action reason is `IMPLEMENTING_READY_STORY_CONTEXT_NEXT` and target is `ui.story-code-workbench` when Planning is complete;
- Planning closure no longer emits historical `GSDLC_09_REQUIRED` at `IMPLEMENTING_READY`;
- Project Status marks Build/Validate current at the story-context boundary;
- existing Planning JSON and six Markdown files remain byte-identical;
- tests/smokes/Vite PASS; full regression remains 0.

## BLOCK criteria

Any contradictory Roadmap next action after `IMPLEMENTING_READY`, unavailable Story Code successor, Planning runtime/projection mutation, test/build failure, unexpected Git path, or attempt to treat the C04_BR_105 backfill as fresh browser E2E evidence.

## Verification commands

```powershell
& "D:\Projects\DevPilot_Local\.venv\Scripts\python.exe" -m pytest -q tests/test_devpl_gsdlc_13_c_04_planning_authoring_bridge.py
```

```powershell
npm.cmd --prefix ui/web run build
```

## Windows post-UI adjudication

C04_BR_107 reached its declared automation and post-UI gates: 58/58 tests PASS, three smokes PASS, Vite PASS, Planning JSON/Markdown unchanged, Roadmap/Backlog/Sprint FROZEN and the global/local next-action label reconciled to Story Code Workbench. Promotion is nevertheless deferred by Owner evidence from `02_c04_107_project_status_build_current.png`.

The full Project Status surface exposed two remaining actionability contradictions not covered by the C04_BR_107 post-ui assertions:

1. the `Próxima acción` card received `ui.story-code-workbench` and marked the action available, but `ProjectStatusView` used a private two-entry navigation map that could not resolve that route id, so the `Continuar` button was disabled with `Destino todavía no disponible en la UI`;
2. `Step Action Advisor` continued to short-circuit on `pre_code_profile.all_stages_frozen` and recommended `Pre-code está READY; la siguiente frontera es Planning`, despite the server-authoritative `current_step=story-context-readiness`.

The Story Code Workbench route already exists (`/story/code`, `ui.story-code-workbench`), so these are functional Guided successor defects rather than missing downstream product capability. C04_BR_108 corrects route resolution and advisor authority ordering before Git promotion.
