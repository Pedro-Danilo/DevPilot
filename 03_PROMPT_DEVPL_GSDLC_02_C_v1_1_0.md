---
doc_id: "DEVPL-PROMPT-GSDLC-02-C"
prompt_number: "03"
title: "Prompt operativo — DEVPL-GSDLC-02-C — RBAC enforcement by endpoint, action and workspace"
status: "ready_for_execution"
version: "1.1.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "owner_approved_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-02"
micro_sprint: "DEVPL-GSDLC-02-C"
execution_rule: "solo este micro-sprint; 02-D bloqueado hasta owner adjudication CLOSED/PASS"
source_authority_mode: "dynamic-predecessor-rebind"
source_repo: "repo_DevPilot_Local_356_DEVPL_GSDLC_02_B_HISTORICAL_CONTRACT_RECONCILIATION.zip"
source_git_commit: "e795e4982b984a9727dd458c71ecd0a5b05e2557"
source_repo_sha256: "f500f9d74f7012d6750a58e6415e18d41642419a887b40f1dcdd954c8323ab5c"
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
source_backlog: "DEVPL-GSDLC-02_local_identity_authenticated_sessions_and_rbac_v1_2_0_APPROVED.md"
local_first: true
dry_run_default: true
external_api_required: false
external_network_required: false
pilot_workspace_mutation_allowed: false
---

# Prompt operativo — DEVPL-GSDLC-02-C

## 0. Rebind de autoridad v1.1.0

Esta versión reemplaza únicamente la autoridad de ejecución del prompt original. La fuente vigente es:

```text
repo
repo_DevPilot_Local_356_DEVPL_GSDLC_02_B_HISTORICAL_CONTRACT_RECONCILIATION.zip

commit
e795e4982b984a9727dd458c71ecd0a5b05e2557

SHA-256
f500f9d74f7012d6750a58e6415e18d41642419a887b40f1dcdd954c8323ab5c

branch
eval/post-h-eval-002-02-a-onboarding
```

`GSDLC-02-B` está `CLOSED/PASS` por `DEVPL_GSDLC_02_B_FINAL_OWNER_ADJUDICATION_v1_0_0.md`.

La historia repo353/repo354/repo355 se conserva como ancestor/evidencia; no es la base operacional de C.

Reglas adicionales de esta ejecución:

- preservar los snapshots `*_gsdlc02a_at_close` y los hechos históricos de B;
- toda evolución de un registry `current-active` debe acompañarse de successor proof y `historical_contract_sweep`;
- el baseline sucesor se empaqueta desde raw Git blobs (`git ls-tree` + `git cat-file`), no mediante `git archive`;
- 02-C no implementa UI de login ni authenticated approval binding final;
- full regression permanece prohibida por rutina en C y diferida a 02-E.


## 1. Mandato

Implementa **solo** `GSDLC-02-C — RBAC enforcement by endpoint, action and workspace` sobre 02-B `CLOSED/PASS`.

Rebind obligatorio al baseline canónico B.


## Fuentes obligatorias de autoridad

Antes de proyectar cualquier cambio, consultar literalmente como mínimo:

- `repo_DevPilot_Local_356_DEVPL_GSDLC_02_B_HISTORICAL_CONTRACT_RECONCILIATION.zip` como baseline canónico vigente y fuente de ejecución de 02-C;
- `DEVPL_GSDLC_02_B_FINAL_OWNER_ADJUDICATION_v1_0_0.md` como autoridad inmediata de cierre del predecesor;
- `DEVPL_GSDLC_01_BACKLOG_CLOSURE_ADJUDICATION_v1_0_0.md`;
- `DEVPL-GSDLC-02_local_identity_authenticated_sessions_and_rbac_v1_2_0_APPROVED.md`;
- `docs/backlogs/POST-H-012_approval_rbac_hardening.md`;
- `docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md`;
- `docs/02_architecture/adrs/ADR-GSDLC-003-local-authenticated-operator-boundary.md`;
- `.devpilot/identity/identity_registry.json`;
- `.devpilot/approval/sensitive_action_catalog.json`;
- `src/devpilot_core/identity/`;
- `src/devpilot_core/approval/`;
- `src/devpilot_core/interfaces/api/security.py`;
- `.devpilot/gsdlc/transversal_validation_policy.json`;
- `.devpilot/project_state.json`;
- Source Registry, schema catalog y TCR v1/v2 vigentes.

Si una fuente obligatoria no está disponible, **BLOCK antes de implementar**. No completar documentación por suposición.


## 2. Modelo de autorización

Introducir un `RBACEnforcer`/equivalente que reciba exclusivamente:

- `AuthenticatedPrincipal`;
- typed action/capability;
- endpoint/operation id;
- workspace scope;
- resource/risk metadata.

Resultado determinístico machine-readable:

- ALLOW/DENY;
- reason code;
- policy/role refs;
- workspace decision;
- effective roles;
- stale-session/role decision.

Unknown action/route/scope = `DENY`.

## 3. Cobertura de superficies

Cruzar como mínimo:

- ApplicationService capabilities;
- API route contract registry;
- sensitive action catalog;
- approval actions;
- workspace operations;
- Git/filesystem actions;
- quality/jobs/AI surfaces;
- Project Status;
- Settings;
- Approval Center.

Clasificar cada current-active route/capability como:

- public-local-bootstrap mínimo;
- authenticated-read;
- authenticated-action;
- approval-authority;
- system/legacy compatibility.

No permitir rutas sensibles unmapped.

## 4. Role/workspace semantics

- roles derivados del principal/session;
- workspace scope obligatorio cuando la operación es workspace-bound;
- cross-workspace deny;
- role changes invalidan o fuerzan reevaluación de sesiones según policy;
- no self-escalation;
- owner recovery separada de role mutation normal;
- legacy role aliases aplican solo vía migration map explícito.

## 5. Capability view para frontend

Exponer un DTO sanitizado derivado del servidor:

- identity summary;
- effective roles;
- allowed/disabled capabilities;
- disabled reason.

La UI puede ocultar/deshabilitar, pero **el servidor sigue siendo la autoridad**.

## 6. Tests obligatorios

- exhaustive role×action matrix;
- route registry coverage 100% para rutas sensibles/current-active;
- unknown action deny;
- role escalation negative;
- workspace scope mismatch;
- role changed/stale session;
- legacy local token cannot reach human-only sensitive actions;
- UI hidden vs API 403 parity;
- direct API bypass negatives;
- A+B+C cumulative regression.


## Política transversal de validación y regresión

1. Ejecutar L0 integrity/authority antes de mutar.
2. Ejecutar focal del micro-sprint y regresión acumulativa de todos los micro-sprints GSDLC-02 ya cerrados.
3. Ejecutar Test Impact siempre en dry-run/analyze.
4. A→D usan `validation_mode=cumulative-selective`.
5. En A→D, `full_regression_required=true` emitido por Test Impact es señal de escalamiento, no orden automática.
6. Full regression intermedia solo por hard trigger sistémico explícito y owner-approved.
7. E ejecuta la única full regression de GSDLC-02 exactamente una vez, después de los gates baratos y browser acceptance real.
8. Si la full de E falla: conservar log original inmutable; corregir causas; selective retest de fallidos + contratos impactados; **no ejecutar una segunda full**.
9. Historical Regression Guard debe recibir evidencia honesta del modo de validación; no usar waiver para ocultar fallos.
10. Nunca relajar tests históricos solo para obtener verde: clasificar `historical-freeze`, `current-active`, `successor-needed`, `deprecated-after-proof`.


Para 02-C: **full regression = NO** salvo hard trigger owner-approved previo.


## Seguridad y límites obligatorios

- localhost/loopback only;
- public API, remote login, tenancy, OIDC/SSO, enterprise IAM permanecen deshabilitados;
- deny-by-default;
- ningún LLM/modelo decide autenticación, roles, RBAC, approvals o session authority;
- passwords/raw credentials nunca en logs/evidence/source;
- session IDs/tokens/cookies/CSRF secrets nunca en source ZIP ni evidence;
- legacy local API token no puede convertirse en principal humano ni autorizar approvals identity-bound;
- no role self-escalation;
- no actor supplied by caller como autoridad de approval;
- toda mutación sigue `plan → dry-run → policy/RBAC → approval → execute → verify → evidence`;
- no `reset --hard`, `clean`, rebase automático ni force push;
- pilot workspace preservado.


## 7. Evidencia mínima

- `rbac_coverage.json`;
- `negative_access_matrix.json`;
- role×route/action coverage;
- unmapped sensitive actions = 0;
- cross-workspace evidence;
- capability-view parity report.

## 8. PASS / BLOCK

PASS-CANDIDATE si:

- 100% sensitive/current actions mapeadas;
- server-side deny funciona independientemente de UI;
- unknown = deny;
- cross-workspace bloqueado;
- role self-escalation imposible;
- UI capability view coincide con server authority;
- S0/S1=0.

BLOCK si UI oculta pero API permite, hay acción crítica unmapped, workspace scope omitido o legacy token elude RBAC.

## 9. Git

Feature: `feat/devpl-gsdlc-02-c-server-rbac-enforcement`

Commit: `feat(gsdlc-02-c): enforce server-side local RBAC`


## Topología y entregables Windows

Usar únicamente las raíces vigentes:

```text
D:\Projects\DevPilot_E2E_Evaluation
D:\Projects\DevPilot_Workspaces\inventory-sales-local
D:\Projects\DevPilot_Artifacts\POST-H-EVAL-002
D:\Projects\DevPilot_Local
```

El prompt ejecutado debe producir:

1. package `.zip` con operador Python state-aware, payload exacto, authority inputs y manifest;
2. delta candidate exacto;
3. repo candidate PRE-WINDOWS limpio, explícitamente no canónico;
4. guía única `.md` para personal no experto;
5. sidecars SHA-256;
6. `SOURCE_DELTA_MANIFEST.json`;
7. `ARTIFACT_HASHES.sha256`;
8. `OPERATION_DECLARATION.json`;
9. `CURRENT.json`;
10. closure report;
11. `historical_contract_sweep`;
12. definición exacta de evidence Windows;
13. feature branch y commit convencional;
14. recuperación focal si hay BLOCK, sin resetear el trabajo válido.

La guía Windows debe usar comandos PowerShell de una sola línea física. Debe auditar sus propias rutas para evitar caracteres de control invisibles o concatenaciones inválidas.
