---
doc_id: "POST-H-EVAL-002-01-D-RUN05B-INTEGRAL-CORRECTIVE-326-REPORT"
title: "POST-H-EVAL-002-01-D — RUN05B forensic audit and integral corrective 326"
status: "implemented-pending-independent-validation"
version: "1.0.0"
owner: "POST-H-EVAL-002-01-D"
updated: "2026-07-28"
phase: "POST-H-EVAL-002"
priority: "P0"
source_repo: "repo_DevPilot_Local_325_POST_H_EVAL_002_01_D_BROWSER_ACCEPTANCE_CORRECTIVE.zip"
target_repo: "repo_DevPilot_Local_326_POST_H_EVAL_002_01_D_RUN05B_INTEGRAL_CORRECTIVE.zip"
required_retest: "PILOT-E2E-001-RUN-05B-RERUN-03"
---

# RUN05B forensic audit and integral corrective 326

## Decision

`PILOT-E2E-001-RUN-05B-RERUN-02` is retained only as forensic evidence and must close as `BLOCK/product-contract-evidence`. It must not run `Finalize`, and none of its browser evidence can be promoted as acceptance evidence for repo 326.

The supplied repo 325 ZIP was verified with SHA-256 `c0d3b54cf6fef983997261e7177717490c881a21fad15fb7f478f30efb412e36`. No previously proposed patch was treated as implemented.

## Evidence truth

- All 13 viewport screenshots and all 5 full-page route screenshots were inspected at original resolution.
- Five normal-route captures show functioning surfaces, but Dashboard lacks a Health preflight, Approval Center shows contradictory unconditional states, and Settings shows token-derived characters.
- Only NEG-01 through NEG-04 semantically prove their declared states.
- NEG-05 shows populated traces instead of empty traces.
- NEG-06 does not show a forbidden-action result.
- NEG-07 does not place `parse_error` in the captured viewport.
- NEG-08 shows a generic API-down state because the timeout fixture failed at the CORS preflight.
- The final HAR contains 60 entries from a short Dashboard/Reports window and proves only 5/23 contractual operations.
- API logs prove 21/23 legitimate UI operations. Missing operations are `api.health` as a Dashboard consumer and `api.actions.dry-run` as an executed browser action.
- The bridge register is legitimately `CLOSED 8/8`: BRIDGE-001..003 are lifecycle references; BRIDGE-004..008 have six successful physical execution results.
- Manual observations remain `PENDING`, have four null confirmations, and cannot support the recorded PASS labels.

## Product corrections in repo 326

1. Dashboard now consumes `client.health()` before protected warm-up, exposes operation id, result and duration, and stops the protected fan-out if Health fails.
2. Dashboard distinguishes five protected data results from six contractual browser operations.
3. Approval Center renders BLOCK only after a blocked dry-run and PENDING only when a requested approval exists.
4. Approval Center treats the unqueried initial state as PENDING, not EMPTY.
5. Settings recursively replaces secret-like visual fields with `<redacted>`; no token-derived prefix or suffix is rendered.
6. Shared state notices expose appropriate `status`/`alert`, `aria-live` and `aria-atomic` semantics.
7. Python and Node gates fail if the Health method again becomes declared-but-unconsumed or if contradictory notices return.

## Deferred operator and auditor corrections

These corrections belong to the execution-tooling sprint before the next authoritative browser run:

- deterministic empty-traces fixture;
- CORS-correct timeout fixture;
- semantic screenshot receipts;
- complete and unfiltered HAR coverage gate;
- lifecycle-aware bridge reconciliation;
- mandatory dry-run action proof;
- mandatory completion of manual confirmations;
- viewport-target gates for NEG-06 and NEG-07;
- secret-safe packaging and registered-PID-only Stop.

## UX backlog

Long traces, raw JSON dominance, bilingual terminology and oversized full-page routes are S2/S3 debt. They are recorded for later sprints because expanding the P0 patch would increase regression risk without being necessary to make the acceptance contract truthful.

## Closure rule

Repo 326 remains `implemented-pending-independent-validation`. It does not close 01-D, does not authorize 02-A and requires the fresh authoritative run `PILOT-E2E-001-RUN-05B-RERUN-03`.
