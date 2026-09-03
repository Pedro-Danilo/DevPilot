---
doc_id: "ADR-FRX-004"
title: "FRX-v2.3-E — One-full hybrid safe-parallel execution"
status: "accepted"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner"
---
# ADR-FRX-004

## Decision
The v2.3 closing full uses one logical collection. Only `PROVEN_PARALLEL_SAFE` nodeids may enter bounded two-worker waves; every other nodeid remains in the manifest-based coarsened serial lane. The one-full budget is sticky and cannot be reset by resume.

## Constraints
No xdist, shell, generic worker pool, comparison full or count50 fallback. Functional FAIL is completion-first; corrective work uses selective/composite recovery.

## PASS/BLOCK
PASS requires exact accounting, zero conflicts/source drift/new flakes, workers<=2 and `second_full=false`.
