---
doc_id: "DEVPL-GSDLC-01-B-WORKFLOW-ENGINE-CONTRACT"
title: "DEVPL-GSDLC-01-B — Deterministic WorkflowEngine contract"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "candidate_pending_windows_owner_adjudication"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-01"
micro_sprint: "DEVPL-GSDLC-01-B"
source_repo: "repo_DevPilot_Local_349_DEVPL_GSDLC_01_A_WORKSPACE_ENGINEERING_STATE.zip"
source_git_commit: "bbb00547a087bd35f92623e6180ba98c170849ba"
source_repo_sha256: "55155735a0ec15942befc933720482ceb879546ebbba7f9e2ae9fb80094f74e1"
---

# DEVPL-GSDLC-01-B — Deterministic WorkflowEngine contract

## 1. Purpose

`WorkflowEngine` converts a versioned `WorkspaceEngineeringState`, a versioned transition specification and deterministic evidence into an explainable `PASS/BLOCK` decision and an optional successor-state preview.

It does not persist state, run tools, invoke models, call external APIs, mutate source or decide approvals.

## 2. Boundary

```text
ApplicationService
→ GuidedSDLCApplicationService
→ GuidedSDLCService
→ WorkflowEngine
→ WorkspaceEngineeringStateRepository (read)
```

No HTTP/UI route is introduced in 01-B.

## 3. Versioned transition contract

Machine source:

```text
.devpilot/gsdlc/workflow_transition_catalog.json
```

Schema:

```text
docs/schemas/guided_sdlc_transition_catalog.schema.json
```

Each transition defines source/target phase+step+lifecycle, deterministic prerequisites, gates, artifact states, approval metadata, risk class, preview permission and evidence references.

The baseline catalog contains 26 sequential phase transitions derived from `MIPS-DOC-003`. It intentionally does **not** encode full artifact dependency semantics; that executable MIPSoftware registry belongs to GSDLC-05.

## 4. Evaluation semantics

Fail-closed conditions include:

- unknown transition;
- source phase/step/lifecycle mismatch;
- `BLOCKED` lifecycle;
- `REVALIDATION_REQUIRED`;
- missing/false prerequisite;
- missing/unaccepted gate;
- artifact state not accepted;
- required approval not approved.

Blockers use stable priority/code/category/subject ordering. Reason codes are sorted and machine-readable.

Gate `WARN` is accepted only when the transition contract explicitly includes `WARN` in `accepted_statuses`; no implicit downgrade occurs.

## 5. Preview

`preview_advance(...)`:

- requires a PASS evaluation;
- builds an immutable successor using `dataclasses.replace`;
- increments sequence exactly once;
- requires caller-supplied `updated_at_utc` for deterministic replay;
- does not save through `WorkspaceEngineeringStateRepository`;
- leaves the input state unchanged.

## 6. Model/agent authority

`TransitionEvidence` accepts only:

```text
prerequisites
gates
artifacts
approvals
references
```

Unknown fields such as `model_decision` or `agent_decision` are rejected. An LLM cannot participate in transition authority.

## 7. Application boundary

01-B exposes two application capabilities:

```text
guided_sdlc.transition.evaluate
guided_sdlc.transition.preview
```

They remain read-only ApplicationService operations. No local API route and no UI route are added until the successor micro-sprint that owns those surfaces.

## 8. Initial-version limitation

This is an **implemented-initial** workflow kernel, not the final industrial workflow registry. Subsequent work must add:

- GSDLC-01-C Project Status / NextAction projection;
- GSDLC-01-D external drift reconciliation;
- GSDLC-01-E API/UI acceptance;
- GSDLC-05 executable MIPSoftware/MIASI artifact dependency registry;
- later role/policy/agent integration.

The invariant introduced here is stable: transition authority remains deterministic and independent of LLM output.
