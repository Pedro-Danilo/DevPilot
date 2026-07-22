# PATCH 323 → 324 — POST-H-EVAL-002-01-D runtime corrective

Source: `repo_DevPilot_Local_323_POST_H_EVAL_002_01_D_UI_ACCEPTANCE_FIX.zip`
Target: `repo_DevPilot_Local_324_POST_H_EVAL_002_01_D_RUNTIME_CORRECTIVE.zip`

## Corrected

- Protected Dashboard warm-up before progressive fan-out.
- Two bounded retries (500/1000 ms) exclusively for network failures represented as status 0.
- Default timeout remains 8000 ms; readiness/providers/provider-plan use bounded 30000 ms.
- Refresh clears stale snapshots, errors and durations.
- Approval, dry-run and provider plan actions expose pending state, disabled controls, `Ejecutando…`, `aria-busy` and live status.
- RUN-02 remains BLOCK; RUN-03 is mandatory.

## Safety

No API route, PolicyEngine, DB schema, external API, remote execution, connector write, plugin execution or workspace behavior was enabled.

## Validation hygiene

- `npm ci` is allowed only for the frontend validation phase.
- Before the full Python no-regression gate, remove `ui/web/node_modules`; historical source-package and visual-product gates deliberately block when runtime frontend dependencies remain inside the source tree.
- Do not weaken `NO_NODE_MODULES_IN_SOURCE` or the Sprint 73 source hygiene contract.
- The five canonical POST-H-EVAL-002 documents must reference repo 324 and required retest `PILOT-E2E-001-RUN-03`.
