---
doc_id: "MP-V2-SECURITY-THREAT-MODEL-SUCCESSOR"
title: "Multiprovider v2 — MP-0 Foundation Security Threat Model Successor"
status: "IMPLEMENTED / SANDBOX-CANDIDATE"
version: "1.0.0"
owner: "Ordóñez"
date: "2026-10-07"
predecessor_authority: "MP-0E @ 0eb19e3fc58eca90ed126f3b552d1a3187ee233b"
scope: "MP-0 Foundation only"
---
# MP-0 Foundation Security Threat Model Successor

## 1. Purpose

This successor models only the Multiprovider Foundation boundaries actually implemented by MP-0B..MP-0E. It does not rewrite historical DevPilot threat models and does not claim provider execution beyond MP-0.

## 2. Assets

- authoritative upstream artifacts and their semantic hashes;
- GenerationRequest canonical inputs;
- ArtifactCandidateEnvelope payload, status, lineage and content hash;
- ArtifactProfile/ArtifactDependencyProfile definitions;
- GenerationRoute/FallbackDecision;
- provider health/configuration projections;
- cost/network policy decisions;
- provenance envelopes and execution receipts;
- prompt references/hashes without raw prompt persistence;
- trace/span evidence;
- human/Owner authority and existing approval/Git/Quality boundaries;
- browser evidence for Guided/Expert provenance UX.

## 3. Trust boundaries

1. **Deterministic core ↔ generation contracts** — providers may propose candidates but cannot mutate source or authoritative lifecycle.
2. **Artifact authority ↔ dependency resolver** — upstream inputs are data and must satisfy authority/freshness/scope/budget rules.
3. **Provider registry/catalog ↔ route resolver** — health/configuration are projections; no provider probe is implied by a static snapshot.
4. **Route resolver ↔ adapter execution** — MP-0 resolves eligibility only; no model adapter call is performed.
5. **Runtime evidence ↔ logs/traces/UI** — secrets must be redacted and provenance/receipts immutable by content.
6. **Backend projection ↔ Guided/Expert UI** — UI must represent route/fallback/cost/network/authority truth without implying execution.
7. **Owner ↔ material authority** — Owner selection/approval remains separate from provider/model/agent output.

## 4. Threat/control matrix

| Threat | Attack/failure mode | Control | Acceptance |
|---|---|---|---|
| MP0-T01 malformed candidate | invalid version/hash/lineage/schema-like payload | typed candidate constructors + fail-closed validation | negative test |
| MP0-T02 stale/tampered candidate | payload changes after content hash | `content_integrity_ok` + downstream hash binding | negative test |
| MP0-T03 stale upstream/context | expired/low-authority/excluded input enters context | dependency authority/freshness/scope/budget resolver | negative test |
| MP0-T04 unsupported route | request selects route not allowed by request/policy | GenerationRouteResolver fail-closed | negative test |
| MP0-T05 provider unavailable | local provider missing/unhealthy | explicit fallback or BLOCK | negative test |
| MP0-T06 budget bypass | estimated cost exceeds CostGuard/policy | pre-call cost decision; no adapter execution | negative test |
| MP0-T07 secret leakage | secret-like metadata enters provenance/receipt/trace | SecretGuard/redaction + no raw credentials | negative test |
| MP0-T08 prompt-derived tool escalation | model/prompt tries to grant shell/tool/source authority | provider authority surface + separate tool/approval authority | negative test |
| MP0-T09 network policy bypass | route/health claims network during MP-0 | DENY policy + immutable no-network health contract | negative test |
| MP0-T10 external implicit execution | external becomes enabled/fallback silently | external disabled; never implicit fallback | negative test |
| MP0-T11 authority spoofing | model response claims PASS/approve/freeze/Git | authoritative gates outside provider contracts | negative test |
| MP0-T12 provenance/receipt tamper | receipt does not bind request/route/provenance | stable canonical hashes | integration test |
| MP0-T13 UI execution ambiguity | read-only preview appears as real inference | explicit `foundation_preview`, NO LLM/network/API, disabled reasons | browser closure |
| MP0-T14 evidence truncation | long Settings full capture clips lower sections | full-surface evidence + collapsible/progressive disclosure + focused supplements | finding/carry-forward |

## 5. Security invariants at MP-0 closure

- provider/model/agent source write authority = false;
- apply/freeze/approval/Quality/Git authority = false;
- arbitrary shell/tool escalation = false;
- external network/provider execution = disabled;
- real model calls = 0;
- model download = 0;
- raw secrets in provenance/receipt/trace = 0;
- deterministic route remains first-class;
- fallback is explicit and Owner-visible;
- cost/network/provider identity are visible in evidence;
- Pilot/project mutation from console = 0.

## 6. Residual risks / carry-forward

- `CAP-13B01-SETTINGS-001`: Settings is not yet a complete persistent provider configuration editor. Carry to the natural provider-configuration evolution; do not implement during MP-0 closure.
- `UX-MP0E-001`: long Settings surfaces can exceed browser full-page capture height. Preserve full captures but continue progressive disclosure/collapsible sections plus focused supplementary screenshots.
- local/external provider execution remains intentionally disabled until later waves provide provider-specific execution and acceptance.

## 7. Supersession semantics

This document is the **current Multiprovider v2 MP-0 threat-model successor**. It supplements, and does not supersede, historical global/auth/enterprise DevPilot security documents outside this subject.

## 8. Closure gate

PASS only when the MP-0F negative/integration suite, documentation governance, browser closure, one authorized logical MP-0 Full Regression, Git postflight and evidence packaging all pass with S0/S1=0.
