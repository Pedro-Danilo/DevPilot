---
doc_id: "ADR-FRX-002"
title: "FRX v2.3-A — Scoped quality execution context and manifest nodeid transport"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "implemented-candidate/pending-windows-validation"
---
# ADR-FRX-002 — Scoped quality execution context and manifest nodeid transport

## Context
FRX-v2.2-D proved that binding tests and nested aggregate gates repeatedly executed expensive canonical components. It also left serial orchestration coupled to Windows command-line length.

## Decision
1. `QualityGate.describe_plan()` exposes composition without runner execution.
2. A `QualityExecutionContext` is created per top-level aggregate invocation. Reuse is permitted only for the same canonical component key, source identity and input signature inside that invocation. There is no persistent/global cache.
3. Nested UI/API and Local Release Candidate aggregates consume the same scoped context and report reuse explicitly.
4. Full-regression shards transport nodeids through an immutable manifest consumed by a pytest selection plugin. Nodeids are no longer passed on the command line.
5. Git-clean source sealing uses bounded Git commit/tree semantics. Dirty Git state blocks immediately; it does not trigger per-file `git hash-object` confirmation.

## Consequences
- Binding-only tests can prove registration without running hardening/industrial.
- Aggregate semantics remain available through canonical executions.
- Duplicate canonical component execution is observable and must remain zero.
- Shards can be coarsened without command-line-length coupling while preserving live per-node outcome receipts.

## PASS/BLOCK
PASS: scoped reuse only, duplicate canonical executions `0`, Git-clean per-file subprocesses `0`, nodeid manifest exact coverage.
BLOCK: global cache, cross-commit reuse, silent duplicate component execution, dirty-source rehash, lost/duplicated nodeid.

## Verification
Use the focal FRX-v2.3-A tests and the Windows operator supplied with the implementation bundle. No full regression and no parallel worker are authorized in A.
