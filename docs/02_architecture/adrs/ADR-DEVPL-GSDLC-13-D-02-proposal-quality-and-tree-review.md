---
doc_id: "ADR-DEVPL-GSDLC-13-D-02-PROPOSAL-QUALITY-TREE-REVIEW"
title: "ADR — Implementation proposal quality gate and integrated tree review"
status: "approved-for-corrective"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-01"
approval: "projected_for_owner_windows_validation"
---

# Context

The first Story implementation proposal proved that proposal-only generation is the correct safety boundary, but its file structure was story-specific and the dedicated proposal panel duplicated Source tree/editor review.

# Decision

1. Keep `ImplementationProposal → human decision → SourceDraftBuffer Set → SourceChangePlan` unchanged as the authority chain.
2. Replace generator v1 with `deterministic-story-implementation-template-v2` for the source-empty RF-001 bootstrap.
3. Materialize explicit `domain`, `application`, `infrastructure` and `test` artifacts aligned to ARC-C02/C03/C04.
4. Use a reusable `products` persistence model; do not couple tables/classes to a Story ID.
5. Do not invent missing product business fields. Preserve opaque attributes until a governed requirement specializes the data contract.
6. Require structured module docstrings in every generated Python artifact.
7. Put proposal files in the existing Source tree as virtual `PROPOSAL` nodes; click opens read-only content in the existing Draft editor.
8. ACCEPT turns the same conceptual files into runtime-only `DRAFT` nodes; only SourceChangePlan/apply may write source.
9. Old v1 proposals become non-acceptable after the corrective.

# Consequences

- human review is denser in information but lower in page complexity;
- proposal generation is more architecture-aligned and future CAP-001 stories can reuse Product/Repository boundaries;
- the current provider remains deterministic/local/preliminary and does not become an LLM/agent;
- technical-scaffold and project metadata/Git baseline gaps remain separate governed concerns.
