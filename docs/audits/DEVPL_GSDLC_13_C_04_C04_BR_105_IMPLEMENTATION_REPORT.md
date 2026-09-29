---
doc_id: "DEVPL-GSDLC-13-C-04-C04-BR-105-IMPLEMENTATION-REPORT"
title: "C04_BR_105 — Planning governance and human projection corrective"
status: "validated-successor-required"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-29"
approval: "owner_checkpoint_2026-09-29_successor_required"
---
# C04_BR_105 — Implementation report

## Scope

C04_BR_105 is a bounded successor corrective over C04_BR_104. It preserves the already FROZEN Greenfield Planning state and addresses four findings discovered before C04_BR_104 promotion:

1. lifecycle actions/selectors were not fully gated by state;
2. internal deterministic templates could be perceived as materialized artifacts while lifecycle was `MISSING`;
3. Sprint lacked a Guided Manual authoring path for story selection/capacity;
4. Planning JSON lacked a durable human-readable companion projection.

## Implemented changes

### Lifecycle hardening

Roadmap, Backlog and Sprint proposal operations now fail closed when the current workbench wrapper is `APPROVED`. `FROZEN` continues to require a successor semantic version. UI actions expose only transitions valid for the current lifecycle; selectors are locked in `APPROVED/FROZEN`.

### Truthful MISSING state

Roadmap/Backlog/Sprint previews explicitly state that no governed artifact has been materialized until Generate/Derive/Manual Save creates a DRAFT. Internal templates are preparation data, not persisted lifecycle state.

### Sprint Guided Manual authoring

Sprint exposes `DevPilot local · derivado` and `Manual`. Manual authoring supports selection of stories from the FROZEN Backlog, estimates, capacity, title, DoR and DoD; test intents/risk focus are recalculated from selected story traceability and the server validator remains authoritative.

### Human-readable Planning projections

The new ADR and this implementation report are registered in `.devpilot/docs_governance/source_registry.json`.

`human_projection.py` generates `roadmap.md`, `backlog.md` and `sprint_plan.md`, plus FROZEN revision projections. JSON remains canonical; every projection is hash-bound to its source JSON object and declares its edit policy.

## Current Greenfield evidence reused

The C04_BR_104 checkpoint is already:

- Roadmap `FROZEN`, 6 milestones, requirement/risk coverage 100%;
- Backlog `FROZEN`, 6 epics, 11 stories, requirement coverage 100%, 0 blockers;
- Sprint `FROZEN`, 8/11 stories selected, capacity/load 8/8, validation PASS, executable true, 0 blockers, no overcommit;
- Planning closure `IMPLEMENTING_READY`.

C04_BR_105 must not regenerate or re-freeze these artifacts. It reconciles Markdown projections from the existing canonical JSON and performs a read-only browser check.

## Validation strategy

- focal: `tests/test_devpl_gsdlc_13_c_04_planning_authoring_bridge.py` — 6 tests;
- GSDLC-08 impact: 44 tests;
- documentation-governance impact: 6 tests (`source_registry` schema + derived summary consistency);
- three static browser/contract smokes;
- Vite build on Windows;
- canonical JSON before/after SHA comparison;
- six Markdown projection hash/frontmatter checks;
- read-only browser evidence over the FROZEN checkpoint;
- exact cumulative Git promotion set;
- **full regression: 0**, because this is an intermediate corrective, not backlog closure.

## Windows checkpoint result

C04_BR_105 v1.0.1 reached automated PASS and post-UI PASS for the declared read-only gate: 56 tests, three smokes, Vite PASS, six projection files present, canonical Planning JSON unchanged, Roadmap/Backlog/Sprint FROZEN and Planning `IMPLEMENTING_READY`. Promotion is nevertheless **deferred to C04_BR_106** because owner evidence exposed a false progress indicator in the Planning critical-path header: it remained `Roadmap=current` after the three Planning artifacts were FROZEN.

The six Markdown files in this already-FROZEN workspace were created by the bounded `reconcile_existing_planning_projections(...)` migration step. They are valid hash-bound projections, but this backfill is **not classified as browser E2E proof of fresh lifecycle generation**. Product lifecycle code itself writes projections on DRAFT/REVIEW/APPROVED/FROZEN; C04_BR_106 adds an explicit regression test that proves those writes without calling reconcile. A future fresh Planning journey must still exercise that behavior through the normal UI before claiming browser-level E2E evidence for projection creation.

## Known limitations

- `DeterministicPlanningCandidateProvider` remains a preliminary deterministic provider; it does not perform intelligent/LLM prioritization.
- Markdown projections are not direct-edit round-trip sources.
- The current Greenfield workspace is FROZEN, so the new Sprint Manual click-path can be validated statically/focally/build-wise now, but its full interactive path must be exercised in the next fresh/successor Planning journey without thawing this baseline.
- The historical SprintPlan payload contains an internal `lifecycle` field while the workbench wrapper is the authoritative lifecycle record. C04_BR_105 does not rewrite FROZEN content hashes to reconcile that inherited redundancy; human/UI projections use the wrapper lifecycle. A future schema cleanup may remove this duplicate representation under a migration contract.

## Risks

- A projection implementation that modifies canonical JSON would invalidate existing approval/freeze hashes.
- Relaxing the new APPROVED proposal block would reintroduce an illegal lifecycle transition.
- Treating derived Markdown as a second authority would create reconciliation ambiguity.

## PASS criteria

- 56/56 Python tests PASS and 3/3 smokes PASS;
- Vite build PASS on Windows;
- 6/6 Markdown projections valid and canonical JSON unchanged;
- FROZEN selectors/actions locked and selected/unscheduled Sprint stories readable;
- `IMPLEMENTING_READY` preserved;
- protected Greenfield source Git state unchanged outside runtime `outputs/**`;
- cumulative corrective commit contains exactly the declared promotion paths;
- full regression count remains 0.

## BLOCK criteria

Any test/smoke/build failure, lifecycle downgrade, projection/hash mismatch, canonical JSON mutation, source-code drift in the Greenfield workspace, unexpected promotion path, mutating Planning POST during the read-only browser gate, or Git 3-state mismatch.

## Verification commands

```powershell
& "D:\Projects\DevPilot_Local\.venv\Scripts\python.exe" -m pytest -q tests/test_devpl_gsdlc_13_c_04_planning_authoring_bridge.py
```

```powershell
npm.cmd --prefix ui/web run build
```
