---
doc_id: "DEVPL-GSDLC-13-C-04-C04-BR-106-IMPLEMENTATION-REPORT"
title: "C04_BR_106 — Dynamic Planning progress and E2E evidence integrity corrective"
status: "POST_UI_PASS_PROMOTION_DEFERRED"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-29"
approval: "owner_evidence_reviewed/c04_br_107_required"
---
# C04_BR_106 — Implementation report

## Objective

C04_BR_106 is a bounded successor over C04_BR_105. It does not alter canonical Planning data, provider semantics, RBAC, lifecycle persistence or Markdown projection architecture. It corrects one reproducible Guided UX contract violation and tightens the evidence contract around human-readable projections.

## Findings addressed

1. **Dynamic progress defect.** `RoadmapWorkbenchView` instantiated `CriticalPathGuidance` with Roadmap permanently `current`, Backlog/Sprint permanently `upcoming`, and a static Roadmap next action. Owner evidence showed this stale header while the server-authoritative state was Roadmap/Backlog/Sprint `FROZEN` and Planning `IMPLEMENTING_READY`.
2. **Projection evidence classification.** The six Markdown files in the existing FROZEN Greenfield workspace were reconciled by the C04_BR_105 operator because those Planning lifecycle transitions occurred before the projection capability existed. This is a legitimate migration/backfill, not normal-user UI E2E evidence of fresh projection generation.

## Implementation

### Dynamic Planning critical path

The header is now derived on every refresh from live Roadmap, Backlog, Sprint and Planning-closure state. It exposes `data-planning-progress` and `data-planning-journey-state` for deterministic verification.

Expected phase mapping:

- Roadmap not FROZEN → Roadmap `current`;
- Roadmap FROZEN and Backlog not FROZEN → Roadmap `done`, Backlog `current`;
- Roadmap+Backlog FROZEN and Sprint not FROZEN → Roadmap+Backlog `done`, Sprint `current`;
- all three FROZEN → all three `done`;
- all three FROZEN + `IMPLEMENTING_READY` → next action points to `13-D-01` Story context pack + implementation route/model policy/provenance.

### Projection evidence integrity

No new projection architecture is introduced. The accepted ADR remains authoritative: JSON is canonical and Markdown is derived.

A new focal test starts from a fresh temporary Planning workspace and proves that normal **product lifecycle methods** create/update `roadmap.md`, `backlog.md` and `sprint_plan.md` at DRAFT → REVIEW → APPROVED → FROZEN, including revision Markdown files, without invoking `reconcile_existing_planning_projections(...)`.

The Windows C04_BR_106 operator performs **zero workspace runtime writes**. It must not recreate, rewrite or reconcile the six existing Markdown files; it snapshots and revalidates their hashes instead.

## Why the C04_BR_105 backfill is not treated as cheating

A corrective that adds a derived artifact to records frozen before the feature existed needs a one-time migration. The backfill is therefore valid as migration evidence and does not alter canonical JSON. It would be invalid to claim that those specific files prove the browser produced them during the historical C04_BR_104 lifecycle. C04_BR_106 explicitly avoids that claim and preserves the distinction between migration evidence, integration proof and future browser E2E proof.

## Validation

- C04 focal suite: expected 7 tests;
- GSDLC-08 impact suite: expected 44 tests;
- docs-governance impact: expected 6 tests;
- three Planning smokes;
- Vite build on Windows;
- read-only browser checkpoint proving dynamic all-done progress and `IMPLEMENTING_READY`;
- canonical JSON hashes unchanged;
- all six existing projection file hashes unchanged;
- Greenfield protected source Git unchanged;
- full regression: 0.

## Risks

- Deriving the header from stale local assumptions rather than server state would reproduce the defect.
- Re-running projection reconciliation in this successor would blur the distinction between migration and normal-product evidence.
- Treating the integration proof as browser E2E proof would overstate acceptance coverage.

## PASS criteria

- dynamic header matches live lifecycle and shows all three steps `done` at `IMPLEMENTING_READY`;
- next action identifies `13-D-01` rather than Roadmap generation;
- 57/57 Python tests PASS and 3/3 smokes PASS;
- Vite build PASS;
- canonical JSON and six Markdown projection hashes unchanged during C04_BR_106;
- no Planning mutating operation and no workspace runtime write is required;
- cumulative Git promotion set is exact;
- full regression remains 0.

## BLOCK criteria

Any stale Roadmap-current header at `IMPLEMENTING_READY`, test/smoke/build failure, canonical JSON/projection mutation, unexpected runtime write, workspace source drift, unexpected promotion path or Git 3-state mismatch.

## Post-UI adjudication

Windows C04_BR_106 reached its declared automated and post-UI PASS gates with 57/57 tests, three smokes, Vite PASS, zero runtime writes and unchanged Planning JSON/Markdown. Promotion is nevertheless deferred: Owner evidence exposed a second cross-surface contradiction outside the local Planning header. The persistent Guided SDLC header still emitted historical `PRE_CODE_READY_PLANNING_NEXT`, and the Planning notice still surfaced terminal `recommended_next=closure`. C04_BR_107 reconciles those successor projections before Git promotion.

## Verification commands

```powershell
& "D:\Projects\DevPilot_Local\.venv\Scripts\python.exe" -m pytest -q tests/test_devpl_gsdlc_13_c_04_planning_authoring_bridge.py
```

```powershell
npm.cmd --prefix ui/web run build
```
