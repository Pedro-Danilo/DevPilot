---
doc_id: "FRX-V2-3-E-IMPLEMENTATION-REPORT"
title: "FRX-v2.3-E — Windows one-full safe-parallel closure — implementation report"
status: "implemented-pending-windows-full"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "pending_windows_validation"
---
# FRX-v2.3-E — Implementation report

## Implemented
- collector CLI accepts the authoritative raw nodeid list emitted by `full_regression_collect_plugin`;
- sealed hybrid plan builder;
- strict serial fallback for all non-PROVEN nodes;
- manifest-coarsened serial lane;
- three-way performance attribution without a comparison full;
- one-full/second-full invariants.

## Validation policy
Local validation is focal/preview only. The unique logical full may run only on the Windows operator.

## Risks
The normalized serial denominator is the sealed known-runtime reference from BR, not a second observed full. Therefore default enablement is conservative: any failure to exceed the owner threshold yields `PASS/AVAILABLE-NOT-DEFAULT`.


## Corrective after the authoritative one-full Windows run

The unique Windows logical full is preserved as immutable evidence: `2909/2909` accounted, `63 FAIL`, `2 ERROR`, `5 SKIP`, `full_runs=1/1`, `second_full=false`. Safety of the bounded parallel scheduler passed; the functional BLOCK was caused by deterministic accumulated contract/governance drift, not by a race or parallel resource collision.

The corrective reconciles: the two E schemas in the global Schema Catalog; current CLI ownership and the eight historically missing CLI bridge capabilities; stale v2.2/v2.3-B/BR historical assertions after A/BR/D evolution; and the missing QualityGate imports in one CI contract test. Closure is allowed only through selective/composite recovery of the original 65 FAIL/ERROR nodeids. The original full accounting and performance report are never rewritten and a second full is forbidden.

Expected composite result after Windows recovery: `2904 PASS / 0 FAIL / 0 ERROR / 5 SKIP / 2909 accounted`. The original incremental parallel improvement remains `24.442726%`, below the owner threshold `30%`; therefore the expected performance disposition is `PASS/AVAILABLE-NOT-DEFAULT`.
