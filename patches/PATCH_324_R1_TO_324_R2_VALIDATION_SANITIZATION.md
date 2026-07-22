# PATCH 324-R1 → 324-R2 — validation sanitization

## Scope

Incremental patch applied on top of `repo_DevPilot_Local_324_POST_H_EVAL_002_01_D_RUNTIME_CORRECTIVE.zip`.

## Root causes corrected

1. Restore the explicit POST-H-015-D safety contract marker `remote_execution_enabled=false` in `OperatorGatePanel.ts`; runtime semantics remain unchanged.
2. Synchronize all five canonical POST-H-EVAL-002 documents with repo 324, RUN-02 `BLOCK` and mandatory `PILOT-E2E-001-RUN-03`.
3. Record validation hygiene: frontend dependencies may be installed for npm/build checks, but `ui/web/node_modules` must be removed before the full Python no-regression gate.

## Explicit non-changes

- No API contract change.
- No PolicyEngine change.
- No DB/schema change.
- No weakening of `NO_NODE_MODULES_IN_SOURCE`.
- No authorization of RUN-03 or POST-H-EVAL-002-02-A.

## Required Windows gate

The full Windows suite must be rerun from a source-clean tree. PASS is required before commit/tag and materialization.
