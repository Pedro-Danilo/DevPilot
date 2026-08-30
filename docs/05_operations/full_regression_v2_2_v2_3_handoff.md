---
doc_id: "DEVPL-FULL-REGRESSION-V2-2-V2-3-HANDOFF"
title: "Full Regression v2.1 → v2.2/v2.3 telemetry handoff"
status: "approved"
version: "1.0.1"
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


## E-03 nodeid normalization invariant
Windows E-03 exposed a v2.1 collection defect: normalizing backslashes across the entire pytest nodeid corrupts escaped parameter ids such as `\t` and `\x7f`. Successor collection must normalize **only** the filesystem path component before the first `::`; the test/item suffix is opaque and must be preserved byte-for-byte.

The consumed v2.1 logical session remains immutable. Because it executed zero terminal nodeids, its recovery is `composite-full-regression-selective-retest` with the corrected 100% uncovered tail plus the bounded corrective tests and Historical Regression Guard. This is not a second logical full session.
