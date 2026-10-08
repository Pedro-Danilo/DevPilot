---
doc_id: "MP1A03-DETERMINISTIC-PROVIDER"
title: "MP-1A-03 Deterministic Product Definition Provider Extraction"
status: "CLOSED / PASS / WINDOWS-ADJUDICATED"
version: "1.0.0"
owner: "Ordóñez"
---
# MP-1A-03 deterministic provider extraction

## Authority

Baseline: `evolution/multiprovider-v2 @ e95ec55a0d238b2fe35810b4994fa25fc17c7951`.

Windows successor: `b28a6111aad4de37b605b76223342f3eb24f77a8` (`33/33 focal`, `12/12 impact`, `1/1 UI smoke`, `7/7 docs`, Full=0).

## Decision

C-01 deterministic Vision/Scope/Requirements generation is now invoked through the shared `GenerationProvider` contract by `DeterministicProductDefinitionProvider`. The proven Markdown renderer is reused unchanged; provider extraction does not grant review, source-write, approval, apply, freeze, Quality or Git authority.

## Parity

Canonical pre-extraction fixtures for Product Vision, MVP Scope and Requirements preserve EOL-normalized content SHA-256. The deterministic provider emits `GenerationRequest` and `ArtifactCandidateEnvelope` metadata while retaining the existing server-authoritative DRAFT → review/diff → approval → apply → FROZEN lifecycle.

## Safety

- model calls: 0
- external API/network: 0
- ExternalModel: disabled
- provider source/apply/freeze authority: none
- Full Regression: 0 for MP-1A-03

## Compatibility

MANUAL and IMPORT origins are unchanged. Decision/semantic-model data remains authoritative input to the deterministic route and existing Decision Inbox/review flows remain unchanged.
