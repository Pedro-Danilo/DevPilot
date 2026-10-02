---
doc_id: "DEVPL-GSDLC-13-D-STORY-CODE-WORKBENCH-OPERATIONAL-CONTRACT"
title: "DEVPL-GSDLC-13-D — Story Code Workbench operational contract"
status: "approved"
version: "1.0.3"
owner: "Ordóñez"
updated: "2026-10-01"
approval: "projected_for_owner_windows_validation"
---

# Scope

This revision supersedes v1.0.2 for D02 continuation. D01 activation/context authority is unchanged.

# Proposal review model

For a source-empty greenfield with Story `IN_PROGRESS`:

```text
StoryContextPack + Architecture FROZEN
→ ImplementationProposal v2 (proposal-only)
→ Source tree virtual PROPOSAL nodes
→ click file → Draft editor read-only review
→ Owner ACCEPT
→ SourceDraftBuffer Set runtime-only
→ Source tree DRAFT nodes
→ edit/recheck
→ one multi-file SourceChangePlan
→ diff/Test Impact/dry-run
→ Owner approval
→ atomic apply
```

There is no separate full-page implementation-proposal surface.

# Generator contract

- provider: `devpilot-local`;
- model/generator: `deterministic-story-implementation-template-v2`;
- network=false;
- external_api=false;
- cost=0;
- preliminary=true;
- source mutations before approved apply=false.

For RF-001 the initial slice must explicitly cover:

- ARC-C02: create-product Application Service;
- ARC-C03: reusable Product domain model;
- ARC-C04: ProductRepository port + SQLite adapter;
- TEST-001: authorization + durable observability.

Story-specific storage names such as `story_rf_001_records` are forbidden by the proposal quality gate.

# Human-review docstring contract

Every generated Python artifact must have a module docstring containing:

- `Purpose:`;
- `Responsibilities:`;
- `Boundaries:`;
- `Traceability:`.

`ACCEPT` is disabled/blocking unless the proposal quality report declares `ready_for_draft_materialization=true`.

# Missing data contract

RF-001 does not define a complete product field schema. DevPilot must not invent SKU/name/price/stock rules. The initial domain representation may preserve opaque attributes and must surface that limitation in proposal quality/provenance.

# Manual authoring

Manual CREATE/EDIT/RENAME remains first-class as an explicit Owner/developer override. It does not become the default source-empty greenfield path and must not infer architecture from placeholders.

# Safety

- proposal files are read-only in the editor before ACCEPT;
- ACCEPT creates only runtime Draft Set;
- old v1 proposals cannot be ACCEPTed after v2 corrective;
- SourceChangePlan remains immutable/exact-path;
- apply remains Owner approval-bound and atomic;
- Full Regression remains 0 in D02.
