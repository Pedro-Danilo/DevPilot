---
doc_id: "ADR-GSDLC-010"
title: "Planning domain lifecycle, traceability and role-bound freeze"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner_prompt"
---
# ADR-GSDLC-010 — Planning domain lifecycle, traceability and role-bound freeze

## Decision

GSDLC-08 planning is a dedicated domain model separated from DTO/UI/runtime persistence. `Milestone`, `Epic`, `Story`, `Sprint`, `Dependency` and `PlanningState` use stable IDs, semantic versions and typed trace links. The lifecycle is explicit: `DRAFT -> REVIEW -> APPROVED -> FROZEN`, with `REVIEW -> DRAFT` as the only correction transition.

Approval and freeze are human authority decisions bound to `owner` or `product-owner`. Agents may draft/suggest in later micro-sprints but cannot approve, freeze or bypass lifecycle. The A implementation is pure/domain-only: it performs no workspace/source writes, network calls, API execution or browser runtime.

Dependencies form a deterministic directed graph. Duplicate IDs, missing endpoints, self-dependencies and cycles BLOCK. Stories require acceptance criteria and at least one requirement trace; all typed trace targets are checked against the caller-supplied authoritative trace set.

## Consequences

- B–E can reuse one lifecycle/graph contract across manual/import/agent authoring.
- Persistence and API/UI adapters remain deferred; A does not create a second authority beside existing RBAC/approval catalogs.
- New tests remain serial by default until isolation evidence explicitly promotes them.
