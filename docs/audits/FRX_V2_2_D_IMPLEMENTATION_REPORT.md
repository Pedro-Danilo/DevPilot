---
doc_id: "FRX-V2-2-D-IMPLEMENTATION-REPORT"
title: "FRX-v2.2-D — Windows one-full benchmark and closure — implementation report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "pending_windows_one_full"
---
# FRX-v2.2-D — Implementation Report

## Baseline and scope
Execution authority is `repo_DevPilot_Local_389_FRX_V2_2_C_TEMPORAL_SCHEDULER_WINDOWS_VALIDATED_CANDIDATE.zip`, Windows commit `503a62d0cd84fade9d057752f3e94de22e9a2c19`, SHA-256 `1f85f58ca3aeb9835f611a1ab792a1e6532be7216364054c46773bbae2b34055`. FRX-v2.2-C is CLOSED/PASS. FRX-v2.2-D is the only v2.2 micro-sprint authorized to consume one logical full regression.

## Implemented
- Git-semantic source fingerprinting based on Git objects/content rather than physical LF/CRLF representation.
- `FullRegressionSessionManager.plan_temporal()` converts the v2.2-C LPT planner into an executable sequential plan while preserving the sealed collection exactly once.
- `OneFullAttemptGuard` persists `attempt=1,max_attempts=1,second_full_allowed=false` and reuses only the same session/source binding.
- `FullRegressionBenchmarkAnalyzer` computes collection overhead, node runtime, process overhead, shard wall-clock max/p95/CV, command chars, infra aborts/resumes and comparison against the sealed 07-E baseline.
- Per-shard runtime evidence now includes immutable receipt + JUnit + outcome JSONL + captured stdout/stderr log with SHA-256, including partial timeout output when available.
- Adoption policy supports only `PASS/ENABLED` or `PASS/AVAILABLE-NOT-DEFAULT` after functional PASS. A functional failure remains BLOCK and cannot trigger another full.
- Duration-history compatibility is Windows + Python 3.12.x + pytest 9.x. Exact reference patch versions remain evidence, not brittle preconditions.

## One-full execution contract
Windows alone consumes the logical full. Pre-full gates must PASS before the marker is created. Shards execute sequentially completion-first. Ordinary FAIL/ERROR does not fail-fast; INFRA_ABORT permits same-session resume of non-terminal nodeids only. A different session/source is rejected by the marker.

## Adoption boundary
The scheduler remains default-disabled before the benchmark. After 100% terminal accounting and zero source drift, Windows compares real metrics to the predeclared thresholds. `PASS/ENABLED` may set the temporal planner as default; otherwise a correct but insufficiently improved run closes as `PASS/AVAILABLE-NOT-DEFAULT` with the feature available but disabled by default.

## Validation before Windows
Only focal contracts are executed locally: one-full/benchmark contract plus directly impacted full-session/planner/registry contracts, Project State, Documentation Drift, Documentation Governance and TCR validation. No local full and no browser are executed.

## Risks and limitations
- v2.2 remains strictly sequential (`workers=1`); it cannot promise a 2× CPU speedup.
- Initial duration history has one sample per nodeid, so realized Windows measurements are authoritative for adoption.
- If the single full reveals functional failures, D does not close immediately and must use bounded selective/composite recovery without a second full.
- v2.3 remains required for safe parallelism and production-grade wall-clock acceleration beyond sequential balancing.

## Current state
Implementation is `PASS-CANDIDATE/PENDING-WINDOWS`. Logical full consumed: `0/1`. Browser: `0`. External API/network are not required for technical PASS.
