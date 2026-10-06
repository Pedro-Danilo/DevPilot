---
doc_id: "MP-V2-PROFILE-DEPENDENCY-EQUIVALENCE"
title: "Multiprovider v2 — Profile, Dependency and Deterministic Equivalence Foundation"
status: "implemented/sandbox-candidate"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-10-06"
program_authority: "DEVPL_MULTIPROVIDER_IMPLEMENTATION_PROGRAM_v2_1_0_APPROVED.md"
sprint: "MP-0C"
---
# Multiprovider v2 — Profile, Dependency and Deterministic Equivalence Foundation

## 1. Purpose

MP-0C establishes how DevPilot describes artifact quality, selects authoritative upstream artifacts, composes bounded context, and verifies deterministic parity without executing a model.

## 2. Reuse decisions

- The existing `validators.artifact_profiles.ArtifactProfile` remains the profile type used by current document validation. MP-0C extends it additively with version/purpose/schema/semantic/completeness/review/downstream metadata.
- `ArtifactProfileRegistry` remains the profile-selection registry. No second registry or profile catalog is introduced.
- `ContextPackV2Builder` remains the sole local RAG/grounding subsystem. The new dependency resolver selects explicit upstream artifact authority and may compose ContextPack v2 as supplementary grounding; it does not index, retrieve, embed or rerank documents.
- Existing C-02 deterministic Technical Design remains unchanged and is used only as a bounded equivalence seam.

## 3. ArtifactProfile foundation

The additive profile metadata covers:

- profile identity/version and purpose;
- required/optional sections;
- payload schema reference;
- semantic/completeness rules;
- upstream trace expectation;
- assumptions/open-question policy;
- prohibited unsupported claims;
- quality gates;
- render template reference;
- human review checklist;
- downstream semantics;
- migration policy.

Historical JSON profiles remain valid and receive conservative defaults. Domain-complete professional Vision/Architecture profiles remain later-wave scope.

## 4. ArtifactDependencyProfile

`ArtifactDependencyProfile` declares required/optional upstream types, minimum authority rank, lifecycle/freshness requirements, namespace constraints, exclusions, context budget, policy/decision references and optional ContextPack v2 grounding.

`ArtifactDependencyResolver` fails closed when a required authority is missing, stale, outside the allowed namespace, explicitly excluded, below authority rank, not in the required lifecycle, or when required inputs exceed the bounded context budget.

The resolver emits `ResolvedArtifactContext` with semantic source hashes, citations, selection/rejection reasons, budget and deterministic `context_sha256`. LF/CRLF differences do not change semantic source hashes.

## 5. ContextPack terminology boundary

- **Dependency context** = explicit authoritative upstream artifact assembly.
- **ContextPack v2** = supplementary local grounding/retrieval already implemented by GSDLC-07-B.
- **Agentic RAG** = not performed by MP-0C.

MP-0C never creates a second RAG subsystem.

## 6. Deterministic equivalence harness

`DeterministicEquivalenceHarness` supports:

- `exact-hash` only where an explicit contract requires byte/structure identity;
- `structural` comparison with LF/CRLF normalization and configurable ignored/unordered paths;
- `semantic-projection` comparison through an explicit deterministic projector.

The harness reports hashes and drift paths. It is designed to detect material semantic drift without making prose snapshots a universal acceptance criterion.

## 7. Authority boundary

Profiles, dependency resolution and equivalence evidence remain proposal/validation infrastructure. They do not grant provider/model/agent source write, approval, freeze, Quality or Git authority.

## 8. Scope exclusions

MP-0C does not implement provider routing/fallback/health, UI, model calls, C-01 provider extraction or domain-complete professional profiles. Full Regression remains `0`.
