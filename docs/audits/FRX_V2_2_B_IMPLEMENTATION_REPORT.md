---
doc_id: "FRX-V2-2-B-IMPLEMENTATION-REPORT"
title: "FRX-v2.2-B — NodeDurationRegistry and robust estimator — implementation report"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-31"
approval: "implementation_candidate"
---
# FRX-v2.2-B — Implementation Report

## Baseline
Execution authority is repo387 Windows validated at commit `9ae471381a081005e2f282f6dabbb6b10607590f`. FRX-v2.2-A is `CLOSED/PASS` and remains immutable.

## Implemented
`NodeDurationRegistry` stores exact pytest nodeids under an explicit environment fingerprint. It ingests sealed telemetry idempotently, rejects malformed/negative durations explicitly, derives `sample_count`, median, p95, robust estimate, min/max, `last_seen`, confidence and cold/warm classification, and exposes status/estimate/preview without executing tests.

The initial source-controlled telemetry snapshot contains the 2,805 terminal samples reconstructed from preserved GSDLC-07-E COMPOSITE-01 receipts: 2,674 PASS, 126 FAIL and 5 approved skips, totaling 12,952.888506 seconds. The initial registry accepts all 2,805 with zero silent omissions.

## Estimator policy
For fewer than three compatible samples, the robust estimate is the median and confidence is low. At three or more samples, an EWMA (`alpha=0.35`) is maintained while median/p95 remain visible. History is separated by environment fingerprint. Aging is policy metadata (`90 day half-life`) and never deletes sealed evidence.

## Safety
`scheduler_enabled=false`, `parallel_workers=1`; duration history cannot authorize parallel safety. No full regression, browser, API/UI runtime or external network is required by this micro-sprint.

## Limitations
The initial historical corpus has one terminal sample per nodeid, so all initial nodeids are correctly classified `cold/low-confidence`. Confidence increases only with compatible future observations. FRX-v2.2-C will consume estimates in shadow/canary planning but is not enabled here.
## Final local focal validation
- NodeDurationRegistry contract: `12/12 PASS`.
- Minimal DocImpact-selected suite: `46/46 PASS`.
- Project State: `PASS`.
- Closure State Consistency / DocumentationDriftGate: `13/13 PASS`, open P0/P1 drift = `0`.
- DocImpactPlanner: `full_regression_required=false`, `browser_required=false`; exactly four focused test files selected.
- Full regression runs: `0`; browser runs: `0`; API/UI runtime startup: `0`.

## Aging clarification
The estimator intentionally keeps `alpha=0.35`. The aging contract is geometric decay, not “the newest sample must outweigh every earlier sample after three observations”. The test asserts that the influence of an old observation decreases by `(1-alpha)` with each compatible successor while every sealed sample remains retained.

## Windows acceptance boundary
Formal `CLOSED/PASS` remains pending Windows execution. The Windows operator must validate the payload using Git-index/canonical-content semantics, run only the four DocImpact-selected focal files plus Project State and Closure Consistency, then apply closure metadata and package repo388. No full regression or browser run is authorized.

