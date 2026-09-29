---
doc_id: "ADR-DEVPL-GSDLC-13-C-04-PLANNING-HUMAN-PROJECTIONS"
title: "Planning canonical JSON with hash-bound human-readable Markdown projections"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-29"
approval: "owner_corrective_C04_BR_105"
---
# ADR — Planning canonical JSON with hash-bound human-readable Markdown projections

## Context

`DEVPL-GSDLC-08` established governed Planning runtime for Roadmap, Backlog and SprintPlan. The canonical persisted records are structured JSON and drive validation, lifecycle, traceability, approval, freeze and closure. During the first Greenfield E2E journey, the Owner confirmed that JSON alone is not an adequate durable reading surface for human review outside the browser, even though the canonical data is technically complete.

Replacing the canonical JSON with Markdown, or allowing two independently editable authorities, would introduce reconciliation ambiguity and would invalidate existing lifecycle/hash contracts.

## Decision

1. **JSON remains the sole canonical authority** for Roadmap, Backlog and SprintPlan runtime state.
2. DevPilot generates a **derived Markdown projection** beside each canonical Planning record:
   - `roadmap.md`;
   - `backlog.md`;
   - `sprint_plan.md`.
3. On `FROZEN`, DevPilot also emits the corresponding immutable revision projection beside the JSON revision.
4. Every Markdown projection contains frontmatter with lifecycle/version/owner/approval plus:
   - `canonical_authority: json`;
   - `source_json`;
   - `source_record_sha256` calculated from the canonical JSON object;
   - `candidate_content_sha256` when available;
   - explicit `edit_policy` directing changes through Planning Workbench.
5. Markdown projections are **not round-trip input** and must not be edited as an alternative authority. Manual authoring remains a governed UI/API operation that produces canonical JSON.
6. Existing FROZEN Planning state may be reconciled by generating missing projections without modifying the canonical JSON bytes.
7. Runtime projections remain under workspace `outputs/planning/...`; they are evidence/operational artifacts, not source-code mutations.

## Lifecycle consequence

The lifecycle remains exactly the contract of `ADR-GSDLC-010`: `DRAFT → REVIEW → APPROVED → FROZEN`, with `REVIEW → DRAFT` as the only correction transition. A proposal over `APPROVED` is fail-closed; a FROZEN same-version proposal is also blocked.

## Security and authority

- Markdown generation performs local filesystem writes only under Planning runtime output directories.
- No network, external API, model or agent execution is introduced.
- Approval/freeze remain human, role-bound and server-authoritative.
- A projection hash mismatch is a BLOCK condition; the JSON source wins and the projection must be regenerated.

## Consequences

### Positive

- Planning becomes inspectable by humans without reading raw JSON.
- Machine consumers keep a single structured authority.
- Frozen evidence remains reproducible and hash-bound.
- No schema migration or dual-write authority is introduced.

### Trade-offs

- Markdown is a projection, not an independently editable docs-as-code source.
- Existing workspaces require one-time projection reconciliation.
- Future Markdown import/export, if desired, requires a separate explicit contract and parser; it is not implied by this ADR.

## PASS criteria

- canonical JSON SHA-256 remains unchanged while reconciling projections;
- all six current main/revision Markdown files contain valid frontmatter and source hash binding;
- Planning Workbench remains the only governed authoring surface;
- no lifecycle downgrade from `APPROVED` to `DRAFT` is possible.

## BLOCK criteria

- JSON and Markdown can diverge without detection;
- Markdown becomes an implicit second authority;
- projection generation changes canonical JSON;
- approval/freeze authority is weakened;
- `APPROVED → DRAFT` becomes reachable.

## Documentation governance

This ADR is registered in `.devpilot/docs_governance/source_registry.json`; its required tests include the C04 planning focal suite and documentation source-registry schema validation.

## Verification commands

```powershell
git -C "D:\Projects\DevPilot_Local" diff -- "docs/02_architecture/adrs/ADR-DEVPL-GSDLC-13-C-04-planning-canonical-json-human-projections.md"
```

```powershell
& "D:\Projects\DevPilot_Local\.venv\Scripts\python.exe" -m pytest -q tests/test_devpl_gsdlc_13_c_04_planning_authoring_bridge.py
```
