---
doc_id: "MP-V2-CANDIDATE-GENERATION-KERNEL"
title: "Multiprovider v2 — Candidate/Generation Contract Kernel"
status: "implemented/windows-validated-candidate"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-06"
program_authority: "DEVPL_MULTIPROVIDER_IMPLEMENTATION_PROGRAM_v2_1_0_APPROVED.md"
sprint: "MP-0B"
---
# Multiprovider v2 — Candidate/Generation Contract Kernel

## 1. Purpose

MP-0B introduces the provider-neutral candidate contract without replacing any current provider, router, lifecycle, approval, Quality or Git authority.

## 2. Reuse decisions

The implementation consumes the MP-0A Reuse/Delta Map:

- preserve `TechnicalDesignCandidateProvider` and add only a compatibility wrapper;
- preserve `PlanningCandidateProvider` and Story implementation proposal contracts;
- preserve `ModelRouterV2`, `ModelAdapterRouter`, `ProviderRegistry`, `ContextPackV2`, CostGuard/ledgers and TraceStore;
- preserve artifact/source lifecycle, approval, Quality and Git boundaries;
- do not introduce model calls, routing runtime, UI or external network in MP-0B.

## 3. New shared contract

`devpilot_core.generation` defines:

- `GenerationRequest` with canonical-input hashing;
- `GenerationProvider<TInput,TPayload>` with generation-only authority;
- `ArtifactCandidateEnvelope<TPayload>`;
- provider/human/agent origin taxonomy;
- candidate lifecycle transitions;
- immutable lineage for regeneration, human edit, provider switch and agent enrichment;
- `CandidateComparisonGroup` for same-input alternatives with Owner-only material selection;
- `DownstreamAuthorityBinding` invalidation when content/input hashes change.

A candidate remains runtime/proposal state. `FROZEN` belongs to the governed artifact lifecycle, not to the candidate.

## 4. Compatibility

`wrap_technical_design_candidate()` wraps the existing C-02 `(content, derivation)` result without changing `pre_code_technical_design.py`, regenerating C-02 artifacts or rewriting historical evidence. Existing Planning and Story candidate/provider implementations remain untouched in MP-0B and are covered by impact tests.

## 5. Authority boundary

Generation providers may produce candidate envelopes. They do not own:

- source writes/apply;
- approval/freeze;
- Quality PASS/BLOCK;
- Git stage/commit/push;
- tool escalation.

Those authorities remain in existing deterministic DevPilot services.

## 6. Validation scope

MP-0B requires focal/domain tests for serialization, lifecycle, lineage, comparison, authority invalidation and provider boundaries, plus impact tests covering the existing Technical Design, Planning and Story implementation candidate seams. Full Regression remains `0`.

## 7. Next boundary

ArtifactProfile/ArtifactDependencyProfile implementation, runtime routing/fallback/cost/health, UI and real model providers remain outside MP-0B.
