---
doc_id: "DEVPL-FULL-REGRESSION-V2-2-V2-3-HANDOFF"
title: "Full Regression v2.1 → v2.2/v2.3 telemetry handoff"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-30"
approval: "approved"
---
# Full Regression v2.1 → v2.2/v2.3 telemetry handoff

## Decision
GSDLC-07-E does not implement v2.2 or v2.3. It only preserves immutable per-node terminal telemetry from the single v2.1 full session.

## v2.2 input
Each terminal sample contains `nodeid`, `outcome` and `duration_seconds`. v2.2 may later derive median, p95, sample count, cold-start separation and shard overhead before designing duration-balanced scheduling.

## v2.3 conservative default
Every node begins `UNCLASSIFIED`, `parallel_safe=false`, `explicit_review_required=true`, `workers=0`. Duration or name alone can never authorize parallel execution.

## PASS/BLOCK
PASS when telemetry is generated from sealed full receipts and parallelism remains disabled. BLOCK if v2.2 scheduling or v2.3 workers are enabled by this sprint.
