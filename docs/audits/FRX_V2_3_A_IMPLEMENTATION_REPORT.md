---
doc_id: "FRX-V2-3-A-IMPLEMENTATION-REPORT"
title: "FRX-v2.3-A — Cost de-duplication and normalized serial baseline — implementation report"
status: "implemented-initial"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "pending-windows-validation"
---
# FRX-v2.3-A — Implementation report

## Objective
Remove demonstrated regression-work duplication before any isolation or parallelism work.

## Implemented
- read-only `QualityGatePlan` / `describe_plan()`;
- invocation-scoped `QualityExecutionContext` with execution/reuse audit;
- nested UI/API and Local Release Candidate component reuse within the same top-level call;
- binding-only QualityGate tests migrated to plan inspection;
- Local Release Candidate structural/CLI/binding tests de-duplicated, with one canonical integral RC execution retained;
- static `AggregateExecutionCostAudit` with a small explicit aggregate-execution allowlist;
- bounded Git commit/tree source seal and dirty-fast-BLOCK semantics;
- nodeid manifest pytest transport with exact selection and live outcome plugin preserved;
- manifest-mode temporal planning and normalized serial shadow baseline;
- v2.2 2844-node collection/session snapshots preserved as immutable performance input.

## Local validation
- exact 8 RUN-06 binding tests PASS in one focal process without aggregate profile execution; local diagnostic wall-clock `5.131 s` versus Windows authority `2931.421 s` (Windows remains acceptance authority).
- canonical Local Release Candidate integral test PASS; structural/schema/CLI/binding tests remain separate and cheap.
- static binding audit PASS with `0` binding-only aggregate runs outside the explicit canonical allowlist.
- canonical hardening execution PASS: `46/46` subgates, `9` explicit scoped result reuses and `duplicate_component_executions_total=0`; measured component wall-time sum `153.545 s` in the local environment.
- normalized v2.2 shadow: `57` count50 processes -> `15` manifest/coarsened shards, `73.684%` reduction, workers=0/full=0.
- current collection shadow: `58` count50 processes -> `15` manifest/coarsened shards, `74.138%` reduction, workers=0/full=0.
- Git-clean source descriptor uses bounded commit/tree semantics with `per_file_git_subprocesses=0`; dirty collect BLOCKs before strong descriptor fallback.
- no full regression, browser, network/external API or parallel worker was used.
- final local focal/impact batch PASS: `19 passed` (FRX-v2.3-A structural/source-seal/manifest tests + exact eight RUN-06 binding contracts + cheap RC schema/CLI/binding contracts).
- final governance reconciliation PASS: Project State, Documentation Governance, Closure State Consistency, TCR v1 and TCR v2 (`307` contracts; only the two inherited non-blocking classification-review warnings remain).

## Risks and limitations
- Windows must prove >=80% wall-clock reduction for the exact eight RUN-06 binding tests versus 2931.421 s.
- Windows must execute exactly one canonical hardening aggregate and verify duplicate canonical component executions = 0.
- No TestIsolationRegistry or parallel worker exists in this sprint.
- The normalized serial baseline is a serial attribution baseline, not a claim of parallel speedup.

## PASS/BLOCK
PASS only when the Windows operator demonstrates the binding cost threshold, aggregate de-dup, Git source-seal invariants and normalized serial shadow invariants without any full regression.

## Windows validation
- Result: `CLOSED/PASS/WINDOWS-VALIDATED`.
- Exact eight RUN-06 binding tests (RUN-00 for this sprint): `2.306 s`; reduction `99.921%` vs `2931.421 s`.
- Canonical hardening: `46` subgates PASS; `duplicate_component_executions_total=0`; scoped reuses `9`.
- Historical normalized shadow after focal Windows duration ingestion: `57 -> 15` processes (`73.684%`).
- Full regression runs: `0`; parallel workers: `0`; browser runs: `0`.
- FRX-v2.3-B authorized.
