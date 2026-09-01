---
doc_id: "FRX-V2-2-C-IMPLEMENTATION-REPORT"
title: "FRX-v2.2-C — Duration-balanced sequential scheduler — implementation report"
status: "implementation-candidate"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "windows_validation_gate"
---
# FRX-v2.2-C — Implementation Report

## Baseline and scope
Execution authority is repo388 Windows validated at commit `228d5dbfb19e10584ed00d616126fe34027d1ba8`. FRX-v2.2-B is CLOSED/PASS. This micro-sprint does not execute or consume a full regression and does not enable parallelism.

## Implemented
- `TemporalShardPlanner`: deterministic LPT/bin-packing over `NodeDurationRegistry`.
- Configurable target 300 s, max 50 nodeids and Windows command bound 7000 chars.
- Estimate > target becomes a slow singleton; unknown nodes preserve exact pytest suffixes and stable ordering.
- Plans expose estimated seconds, confidence, known/unknown counts, command chars and duration-registry provenance.
- CLI `tests temporal-planner preview|shadow-compare` is preview-only and never executes tests.
- Existing `FullRegressionSessionManager.plan()` remains unchanged; adoption is reserved for FRX-v2.2-D.

## Shadow comparison
Same 2,805-node reference collection for both planners. Count baseline: 57 shards, max 1815.940795 s, p95 1458.766241 s, CV 1.763719. Temporal: 71 shards, 15 slow singletons, max 774.736226 s, p95 538.567238 s, CV 1.081476. Predicted improvements: max 57.337%, p95 63.081%, CV 38.682%. These are model predictions, not realized wall-clock claims.

## Canary and safety
Bounded four-node canary executes sequentially with workers=1 in temporal-plan order. Scheduler remains disabled/default false; full=0, browser=0, network/API=0.

## Performance engineering
Duration registry is loaded once per plan and Windows command-length counters are incremental, avoiding O(nodeids × registry-file-read) and repeated command reconstruction.

## Limitations
Initial history remains one observation per nodeid and low-confidence. FRX-v2.2-D must perform the single real full benchmark and adoption decision. v2.3 owns safe parallelism.

## Windows acceptance boundary
Formal CLOSED/PASS requires only focal planner tests, bounded canary, Project State, Closure Consistency, DocImpact, canonical-content payload application, clean repo389/components packaging and Git three-state reconciliation. No full/browser is authorized.
