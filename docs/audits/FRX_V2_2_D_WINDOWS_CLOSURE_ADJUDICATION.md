---
doc_id: "FRX-V2-2-D-WINDOWS-CLOSURE-ADJUDICATION"
title: "FRX-v2.2-D — Windows composite recovery closure adjudication"
status: "closed"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-02"
approval: "windows_validated_composite_recovery"
---
# FRX-v2.2-D — Closure adjudication

## Decision
`CLOSED/PASS` by composite selective recovery. The only logical full remains immutable as `2795 PASS / 44 FAIL / 0 ERROR / 5 SKIP / 2844 accounted`. Recovery v1.0.4 resolved 31 of those nodeids and recovery v1.0.6 resolved the remaining 13; the union is the exact original 44/44. No second full was executed.

## Performance adjudication
The temporal scheduler is retained as `PASS/AVAILABLE-NOT-DEFAULT`. The corrective removes per-shard per-file Git rehashing, adds end-to-end wall-clock accounting and raises the sequential target shard duration to 900 s.

## Successor
FRX-v2.3-A is authorized with the runtime-weighted/Amdahl feasibility prerequisite.

## PASS/BLOCK
PASS: original full preserved, composite node accounting 44/44, post-recovery governance/RC/CLI gates PASS, full runs total 1, second_full=false. BLOCK otherwise.
