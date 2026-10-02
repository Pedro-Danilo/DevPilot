---
doc_id: "DEVPL-GSDLC-13-D-02-DRAFT-PLAN-GOVERNANCE-ADJUDICATION"
title: "13-D-02 RUN_02 — Draft/preimage and governed SourceChangePlan adjudication"
status: "BLOCK / FUNCTIONAL-UX / ACTIVE-CORRECTIVE-REQUIRED"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-02"
approval: "projected_for_owner_corrective"
---

# Adjudication

RUN_02 was intentionally stopped before `recheck + dry-run`. The stop is accepted.

## Findings

### FUNC-UX-13D02-DRAFT-PREIMAGE-013 — S1

The Draft toolbar remained visible during PROPOSAL read-only review because author CSS `display:flex` overrode the HTML `hidden` state. `Revalidar preimage` and `Descartar draft` also lacked state-derived disabling. After a Draft preimage PASS, the shared feedback persisted while another Draft was selected, making a per-file result appear global.

### FUNC-GOV-13D02-DRYRUN-014 — S1

After SourceChangePlan creation, `Revalidar plan`, `Dry-run` and `Solicitar approval owner` were simultaneously enabled. The backend approval-request path revalidated the plan but did not require evidence that dry-run had run. This violated the declared mandatory order and allowed a caller to skip dry-run.

### UX-P1-13D02-012 — S2 absorbed

`Guardar draft` was ambiguous after Proposal ACCEPT already materialized Drafts. Correct semantics: ACCEPT creates the initial Draft Set; Save only persists subsequent human edits/manual authoring. Existing Drafts now use `Guardar cambios en draft`, disabled until dirty.

### UX-P1-13D02-013 — S2 absorbed

Governed source change did not explain the Owner's decision responsibility. A structured Owner review block now explains allowlist/diff/risk/Test Impact review and requires explicit confirmation before dry-run/approval progression.

### TEST-IMPACT-13D02-014 — REVIEW / non-blocking for D02

The current preview reports four unmatched paths, zero matched Test Contracts and zero recommended tests. Analyzer execution PASS is not coverage PASS. This remains reviewable in D02 and must be classified as unknown impact in D03; the UI now says so explicitly.

## State preservation

- repo458 remains the Windows-validated base;
- Story remains `story-rf-001 / IN_PROGRESS`;
- current Draft Set and historical SourceChangePlan are preserved as evidence;
- source remains unchanged before apply;
- corrective continuation rechecks all four existing Drafts and creates a fresh immutable successor plan rather than deleting the historical plan;
- Full Regression remains `0`.
