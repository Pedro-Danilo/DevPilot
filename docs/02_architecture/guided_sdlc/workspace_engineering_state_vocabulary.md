---
doc_id: "DEVPL-GSDLC-01-A-STATE-VOCABULARY"
title: "WorkspaceEngineeringState v1 — lifecycle vocabulary"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "pending_owner_01_a_adjudication"
program_id: "DEVPL-GSDLC"
micro_sprint: "DEVPL-GSDLC-01-A"
---
# WorkspaceEngineeringState v1 — lifecycle vocabulary

## Purpose

`WorkspaceEngineeringState` is the durable per-workspace engineering aggregate. It does not replace Git, canonical documents, `.devpilot/project_state.json`, approvals or runtime job/session stores.

## Engineering lifecycle

`NEW → IN_PROGRESS → READY_FOR_RELEASE → RELEASED` is the nominal progression. `BLOCKED` and `REVALIDATION_REQUIRED` are explicit non-terminal conditions.

`REVALIDATION_REQUIRED` dominates an apparently approved artifact after external/source fingerprint drift. GSDLC-01-D implements the reconciler that sets this condition; 01-A only defines the durable vocabulary.

## MIPSoftware phase vocabulary

The `phase` enum maps MIPSoftware phases 0–25 into stable identifiers from `INTAKE` through `RETIREMENT`, plus `NOT_STARTED`. The state keeps `current_step` as a bounded identifier so GSDLC-05 can bind executable MIPSoftware registries without changing the v1 aggregate shape.

## Artifact substate

The artifact lifecycle anticipates the GSDLC-FR-006 contract: `MISSING → DRAFT → VALIDATING → FINDINGS → READY_FOR_REVIEW → APPROVAL_REQUIRED → APPROVED → FROZEN`, with `REVALIDATION_REQUIRED` as drift state.

## Separation

- PlatformState: product/program governance only.
- WorkspaceEngineeringState: project engineering progress and fingerprints.
- RuntimeOperationalState: sessions/jobs/approvals/locks/agent runs.

Runtime IDs, secrets, credentials, approval payloads and logs are forbidden in this aggregate.
