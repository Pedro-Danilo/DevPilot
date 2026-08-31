---
doc_id: "DEVPL-GSDLC-07-E-IMPLEMENTATION-REPORT"
title: "GSDLC-07-E — Implementation report"
status: "CLOSED/PASS"
version: "1.0.6"
owner: "DEVPL-GSDLC-07-E"
updated: "2026-08-31"
approval: "approved_by_owner"
---
# GSDLC-07-E — Implementation report

## Implemented
`AgenticPrecodeAcceptanceEvaluator` provides a deterministic acceptance projection for five selected pre-code steps. `AgentEvalTraceView` exposes sealed trace/provenance/cost/human-decision evidence through a read-only API projection. `FullRegressionTelemetryExporter` preserves terminal node duration samples for v2.2 while keeping v2.3 disabled.

## Security
Mock/fake-local mandatory for PASS; no external API required. `filesystem.delete` containment, server-side cost hard-stop and human-checkpoint handoff are demonstrated. Model routing never grants tool execution authority.

## Corrective E-02 — API/RBAC parity

Windows browser evidence exposed a current-active integration defect before browser acceptance: `GET /api/v1/settings/agent-evals` existed in API policy/OpenAPI but was absent from the deny-by-default server RBAC catalog. The successor registers the route as human-session-required, legacy-token-denied and read-only, and adds a parity regression that requires every protected `API_ROUTE_POLICIES` entry to exist in `server_rbac_policy_catalog.json`. The corrective does not relax RBAC and does not consume the single full-regression session.

## Corrective E-03 — pytest nodeid preservation
Windows E-03 proved that the v2.1 collector normalized `\` across the complete pytest nodeid. Two parameterized API-security nodeids were therefore sealed as `tab/tinside` and `control/x7f` instead of preserving pytest escape sequences `tab\tinside` and `control\x7f`. Pytest rejected the corrupted selections before executing any test, so the original logical session remains preserved with 0/2803 terminal outcomes and cannot be restarted.

The successor normalizes only the path component before `::`, adds an end-to-end regression for escaped parameter ids, and requires recovery through the original session evidence plus a composite 100% uncovered-tail retest. `full-start` remains permanently unavailable after the existing marker.

## Full regression
Windows consumed the single logical session exactly once. FULL-01 is frozen as `BLOCK/INFRA` with `0/2803` terminal nodeids because the sealed v2.1 collection corrupted two parametrized pytest ids before any test executed. `full-start` and `full-resume` are no longer valid recovery actions for this incident. Closure must use the bounded E-03 source corrective followed by the composite corrected uncovered tail, Historical Regression Guard and terminal accounting; this does not create a second logical full session.

## Preliminary limitations
This is the first version of AgentEvalTraceView and telemetry handoff. v2.2 must design the duration registry/scheduler from real telemetry; v2.3 requires explicit isolation review before any worker is enabled.

## PASS/BLOCK
Browser acceptance is already PASS and is reusable only with a runtime-equivalence receipt because E-03 changes testing/governance/documentation bytes only. Source corrective is PASS locally. Final closure remains BLOCK until composite recovery reaches 100% terminal accounting, Historical Regression Guard passes, packaging completes and Git three-state evidence converges.


## Corrective E-04 — terminal failure decomposition
The preserved E-03 composite reached 2805/2805 terminal outcomes: 2674 PASS, 126 FAIL, 5 approved skips and zero unexecuted. Raw shard JUnit/log/outcome evidence showed that the 126 FAIL collapse into a smaller set of current-active/historical contract drift, registry parity, release-candidate freshness, lazy service-boundary and documentation false-positive causes. The corrective preserves historical checkpoints instead of moving global state backward. Windows closure is limited to the original 126 failed nodeids, bounded impacted tests and the Historical Regression Guard. No second full is authorized.

## FRX v2.2 preparation
E-04 telemetry provides 2805 per-node terminal duration samples. `docs/audits/DEVPL_GSDLC_07_E_FRX_V2_2_TEMPORAL_HANDOFF.json` prepares deterministic duration-balanced sequential scheduling. It remains disabled in 07-E: `scheduler_enabled=false`, v2.2 `parallel_workers=1`; v2.3 remains `UNCLASSIFIED`, `parallel_safe=false`, `workers=0`.


## Corrective E-09 — historical capability snapshot vs current-active registries
Windows v1.0.9 completed the residual selective recovery at 126/126 PASS and then blocked only in Historical Regression Guard because the immutable UOC-011 closure assertion still read the mutable UI Capability Registry and required exactly 193 entries after GSDLC-07 legitimately registered six `tests full-session` capabilities (current total 199). Forward audit found the same stale exact-total assumption in `uoc011_hardening.py` and found the Governed Job Capability Registry still covering only 193 current capabilities.

E-09 preserves the historical UOC-007/UOC-011 fact as explicit `*_at_close=193`, derives current-active summaries from all 199 live capabilities, and registers the six Full Regression v2.1 capabilities in the governed-job registry as `registry-only`. `run` and `resume` are sensitive/approval-bound in the governed contract; none of the six gains a UI/API execution adapter. Browser runtime bytes are unchanged, FULL-01 remains consumed exactly once, and a second full remains prohibited.

Current closure state: selective/composite successor recovery PASS; E-09 focused governance tests PASS locally; Windows Historical Regression Guard, closure gates, Git three-state reconciliation and final packaging remain pending.


## Windows closure E-09
Closure is authorized only after the E09 expanded Historical Regression Guard and deterministic closure gates pass on the corrective commit. The original FULL-01 remains preserved as the single consumed logical full session; no second full was executed. Browser acceptance is reused by runtime-byte equivalence because E09 changes governance/tests/documentation only. The Windows validated successor is repo386, and GSDLC-08 is authorized by the approved backlog while Full Regression v2.2 temporal-distribution work remains the recorded next engineering optimization.
