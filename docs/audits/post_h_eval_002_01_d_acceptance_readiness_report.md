---
doc_id: "POST-H-EVAL-002-01-D-ACCEPTANCE-READINESS"
title: "POST-H-EVAL-002-01-D — Web UI acceptance readiness"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-16"
approval: "IMPLEMENTED-PENDING-WINDOWS-BROWSER-EVIDENCE"
---

# POST-H-EVAL-002-01-D — Web UI acceptance readiness

## Decision

`IMPLEMENTED / OPEN`. The platform is prepared for the formal Windows browser
acceptance, but `POST-H-EVAL-002-01-D` is **not closed** because the required
screenshots, five-route matrix, eight negative-state matrix, UI eligible
operation coverage and initial CLI bridge evidence have not yet been executed
by the operator.

## Incoming baseline

- governance/source: `repo_DevPilot_Local_321_POST_H_EVAL_002_01_C.zip`;
- executable lineage: `repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip`;
- 01-C decision: `closed/PASS-WITH-GAPS`;
- 01-C focal verification: `30 passed`;
- Project State, Documentation Governance, TCR v1/v2 and Evidence Freshness: PASS.

## Acceptance blockers discovered before manual evidence

### EVAL-002-01-D-S1-001 — runtime route dispatch drift

The UI Route Contract Registry declares five critical paths, but the incoming
`ui/web/src/main.ts` always rendered `Dashboard`. Vite returned the SPA shell
for `/reports`, `/traces`, `/approvals` and `/settings`, yet the runtime did not
dispatch the selected path to the registered page component.

Impact: the formal five-route acceptance could not distinguish route success
from SPA fallback success.

Correction:

- route-aware dispatch for `/`, `/reports`, `/traces`, `/approvals`, `/settings`;
- persistent local navigation with `aria-current`;
- controlled unknown-route state;
- no router dependency and no external network.

### EVAL-002-01-D-S1-002 — unbounded browser request

The incoming API client used `fetch` without an `AbortController` or bounded
deadline. The mandatory slow-operation/timeout negative state could remain
pending indefinitely and could not satisfy the recovery criterion.

Correction:

- default timeout `8000 ms`;
- configurable bounded range `1000..60000 ms`;
- controlled `DevPilotApiError` with state `timeout`;
- no token in URL and session-only token storage preserved.

## Scope boundary

This patch does not:

- close 01-D;
- create `inventory-sales-local`;
- add external APIs;
- enable remote execution, connector write or plugin execution;
- relax PolicyEngine, approval, RBAC or no-go gates;
- create screenshots or invent browser evidence.

## Verification implemented

- static route/timeout acceptance baseline script;
- focal Python contract;
- TypeScript compile check;
- existing npm smoke/visual/operator-flow/route-enforcement remain required on
  Windows after materialization;
- operator bundle produces evidence only after manual completion.

## Remaining work

The operator must execute the Windows bundle, visit all five routes, execute all
eight negative states, capture sanitized screenshots, complete the CLI bridge
register and obtain:

```text
Critical Route Coverage = 5/5
UI Eligible Coverage = 100%
secret_exposure = 0
unhandled_errors = 0
S0/S1 open = 0
```

Only then may governance close 01-D and authorize `POST-H-EVAL-002-02-A`.
