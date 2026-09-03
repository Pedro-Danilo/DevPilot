---
doc_id: "FRX-V2-3-E-IMPLEMENTATION-REPORT"
title: "FRX-v2.3-E — Windows one-full safe-parallel closure — implementation report"
status: "implemented-pending-windows-full"
version: "1.0.0"
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
