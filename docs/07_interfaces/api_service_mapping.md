---
title: "DevPilot Local — API v1 service mapping"
doc_id: "DEVPL-INTERFACE-API-SERVICE-MAPPING-V1"
status: "approved"
approval: "approved_after_func_sprint_68_api_security"
version: "1.3.0-web-ui-consumed"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-69"
updated: "2026-06-15"
source_contract: "docs/07_interfaces/api_contract_v1.md"
source_openapi: "docs/07_interfaces/openapi_v1.json"
server_implemented: true
security_implemented: true
---

# DevPilot Local — API v1 service mapping

## Estado

`approved` / `secured-initial` para `FUNC-SPRINT-68`.

## Propósito

Garantizar trazabilidad explícita entre cada endpoint `/api/v1`, la operación de `ApplicationService v2`, el servicio de dominio responsable, el comando CLI equivalente y los controles de seguridad ejecutables.

## Alcance

Este mapping queda sincronizado con el servidor FastAPI local MVP y con la capa de seguridad de Sprint 68. Su función es bloquear dos riesgos: que la API importe motores internos directamente y que la Web UI futura duplique lógica del core o se salte token/policy checks.

## Matriz endpoint → ApplicationService

| API ID | Método | Path | Operation | Domain service | Side effect | Auth | Policy/gate |
|---|---|---|---|---|---|---|---|
| `API-WORKSPACE-STATUS` | `GET` | `/api/v1/workspace/status` | `workspace.status` | `WorkspaceApplicationService.status` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow` |
| `API-VALIDATION-FRONTMATTER` | `POST` | `/api/v1/validation/frontmatter` | `validation.frontmatter` | `ValidationApplicationService.validate_frontmatter` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine + lower PathGuard` |
| `API-VALIDATION-ARTIFACT` | `POST` | `/api/v1/validation/artifact` | `validation.artifact` | `ValidationApplicationService.validate_artifact` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine + lower PathGuard` |
| `API-VALIDATION-READINESS` | `POST` | `/api/v1/validation/readiness` | `validation.readiness` | `ValidationApplicationService.readiness` | `report_when_adapter_requests_it` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow` |
| `API-MIASI-STATUS` | `GET` | `/api/v1/miasi/status` | `miasi.validate` | `MiasiApplicationService.validate` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow` |
| `API-REPO-INVENTORY` | `GET` | `/api/v1/repo/inventory` | `repo.inventory` | `RepoApplicationService.inventory` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow` |
| `API-REVIEW-CODE` | `POST` | `/api/v1/review/code` | `review.code` | `ReviewApplicationService.code_review` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow; dry-run only` |
| `API-REFACTOR-PLAN` | `POST` | `/api/v1/refactor/plan` | `refactor.plan` | `RefactorApplicationService.plan` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow; plan-only; no patch execution` |
| `API-MODEL-PROVIDERS` | `GET` | `/api/v1/model/providers` | `model.providers` | `ModelApplicationService.providers` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow; no external API` |
| `API-OBSERVABILITY-TRACES` | `GET` | `/api/v1/observability/traces` | `observability.trace_report` | `ObservabilityApplicationService.trace_report` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow; bounded read` |
| `API-OBSERVABILITY-METRICS` | `GET` | `/api/v1/observability/metrics` | `observability.metrics_summary` | `ObservabilityApplicationService.metrics_summary` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow; bounded read` |
| `API-HISTORY-RUNS` | `GET` | `/api/v1/history/runs` | `history.runs` | `HistoryApplicationService.list_runs` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow; bounded LocalStore read` |
| `API-APPLICATION-CONTRACT` | `GET` | `/api/v1/application/contract` | `app.contract` | `ApplicationService.application_contract` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow` |
| `API-STANDARDS-STATUS` | `GET` | `/api/v1/standards/status` | `standards.status` | `ValidationApplicationService.standards_status` | `none` | `local-token-required` | `API_ROUTE_POLICIES → PolicyEngine read allow` |

## Reglas de implementación vigente y futura

1. El handler HTTP debe construir un `ApplicationRequest`.
2. El handler debe llamar `ApplicationService.handle()` o un método de dominio expuesto formalmente.
3. El handler debe devolver `ApplicationResponse`.
4. El handler no debe importar directamente validators, repo analyzers, ReviewEngine, RefactorPlanner, ModelAdapterRouter, LocalStore ni TraceStore.
5. Cada ruta protegida debe estar cubierta por `API_ROUTE_POLICIES`.
6. Acciones críticas siguen bloqueadas hasta contar con approval explícito y no se implementan en Fase F temprana.

## Criterios PASS

- Cada path de `openapi_v1.json` aparece en esta matriz.
- Cada operation coincide con `ApplicationService.application_contract()`.
- Cada endpoint declara side effect, auth y policy binding.
- No hay rutas mutantes como patch apply, rollback execute o refactor execute.
- El estado de ruta es `secured-initial`.

## Criterios BLOCK

- Endpoint sin `operation`.
- Endpoint sin servicio de dominio.
- Endpoint que apunte a filesystem/UI directamente.
- Endpoint crítico sin Approval planificado.
- Endpoint protegido sin token local o sin `PolicyEngine`.

## Consumidor Sprint 69 — `ui/web`

La Web UI local consume las siguientes operaciones mediante API local segura:

| Vista | Endpoint | Operación | Acción UI |
|---|---|---|---|
| Dashboard Workspace | `GET /api/v1/workspace/status` | `workspace.status` | tarjeta PASS/WARN/BLOCK |
| Dashboard Readiness | `POST /api/v1/validation/readiness` | `validation.readiness` | tarjeta readiness |
| Dashboard Standards | `GET /api/v1/standards/status` | `standards.status` | tarjeta standards |
| Dashboard MIASI | `GET /api/v1/miasi/status` | `miasi.validate` | tarjeta MIASI |

Regla: el frontend no puede saltar este mapping ni llamar módulos internos.


## Mapping Sprint 70 — Report/Trace Viewer

| API ID | Método | Path | Operación | Servicio | Policy/gate |
|---|---|---|---|---|---|
| API-REPORTS-LIST | GET | `/api/v1/reports` | `reports.list` | `ReportsApplicationService` | Token + PolicyEngine + redacción |
| API-REPORTS-READ | GET | `/api/v1/reports/{report_id}` | `reports.read` | `ReportsApplicationService` | Token + basename seguro + redacción |
| API-TRACES-LIST | GET | `/api/v1/traces` | `observability.trace_report` | `ObservabilityApplicationService` | Token + límites |
| API-TRACES-INSPECT | GET | `/api/v1/traces/{trace_id}` | `observability.trace_inspect` | `ObservabilityApplicationService` | Token + límites |
| API-METRICS-SUMMARY | GET | `/api/v1/metrics/summary` | `observability.metrics_summary` | `ObservabilityApplicationService` | Token + límites |

Regla: UI no lee `outputs/` ni `.devpilot/`; todo pasa por API local.


## Mapeo FUNC-SPRINT-71

| Endpoint | Operación | Servicio | Control |
|---|---|---|---|
| `/api/v1/approvals` | `approvals.list` | `ApprovalApplicationService` | Token + policy binding |
| `/api/v1/approvals/request` | `approvals.request` | `ApprovalApplicationService` | Registro auditado local |
| `/api/v1/approvals/{approval_id}/approve` | `approvals.approve` | `ApprovalApplicationService` | Transición controlada |
| `/api/v1/approvals/{approval_id}/deny` | `approvals.deny` | `ApprovalApplicationService` | Transición controlada |
| `/api/v1/actions/dry-run` | `ui.actions.dry_run` | `ApplicationService` | Dry-run only + PolicyEngine |


## Policy/gate mapping FUNC-SPRINT-71

| API ID | Endpoint | Operación | Servicio | Policy/gate |
|---|---|---|---|---|
| API-APPROVALS-LIST | `/api/v1/approvals` | `approvals.list` | `ApprovalApplicationService` | Policy/gate: token + CORS + API_ROUTE_POLICIES |
| API-APPROVALS-SHOW | `/api/v1/approvals/{approval_id}` | `approvals.show` | `ApprovalApplicationService` | Policy/gate: token + CORS + API_ROUTE_POLICIES |
| API-APPROVALS-REQUEST | `/api/v1/approvals/request` | `approvals.request` | `ApprovalApplicationService` | Policy/gate: token + approval workflow validation |
| API-APPROVALS-APPROVE | `/api/v1/approvals/{approval_id}/approve` | `approvals.approve` | `ApprovalApplicationService` | Policy/gate: controlled state transition |
| API-APPROVALS-DENY | `/api/v1/approvals/{approval_id}/deny` | `approvals.deny` | `ApprovalApplicationService` | Policy/gate: controlled state transition |
| API-ACTIONS-DRY-RUN | `/api/v1/actions/dry-run` | `ui.actions.dry_run` | `ApplicationService` | Policy/gate: PolicyEngine dry-run; no patch execution |


## FUNC-SPRINT-72 — Settings UI mappings

| API ID | Endpoint | Operation | ApplicationService method | Side effect | Policy |
|---|---|---|---|---|---|
| API-SETTINGS-WORKSPACE | `GET /api/v1/settings/workspace` | `settings.workspace` | `SettingsApplicationService.workspace` | read-only | token + PolicyEngine |
| API-SETTINGS-PROVIDERS | `GET /api/v1/settings/providers` | `settings.providers` | `SettingsApplicationService.providers` | read-only redacted | token + PolicyEngine |
| API-SETTINGS-POLICY | `GET /api/v1/settings/policy` | `settings.policy` | `SettingsApplicationService.policy` | read-only redacted | token + PolicyEngine |
| API-SETTINGS-PROVIDERS-PLAN | `POST /api/v1/settings/providers/plan` | `settings.providers.plan` | `SettingsApplicationService.provider_plan` | plan-only, no write | token + PolicyEngine |

Sprint 72 mantiene la regla API-only: la Web UI no lee `.devpilot/`, `outputs/` ni policy/provider files directamente.


## FUNC-SPRINT-73 — Cierre Fase F

No se agregan rutas nuevas. El mapping queda congelado como superficie visual MVP inicial: dashboard, reportes, trazas, approvals y settings. `scripts/visual_product_smoke.py` verifica que las rutas publicadas por OpenAPI sigan alineadas con `ApplicationService` y que no existan rutas críticas libres.


## POST-H-015-C — Operator dashboard ApplicationService/API

POST-H-015-C extiende la superficie `/api/v1` sin habilitar capacidades remotas ni acciones destructivas. La ruta queda protegida por token local, `API_ROUTE_POLICIES`, `PolicyEngine` y `ApplicationService`.

| API ID | Método | Path | Operation | Domain service | Side effect | Auth | Policy/gate |
|---|---|---|---|---|---|---|---|
| `API-OPERATOR-DASHBOARD` | `GET` | `/api/v1/operator/dashboard` | `operator.dashboard` | `OperatorDashboardApplicationService` | `read_only_optional_outputs_reports` | `local-token-required` | `Policy/gate: token + CORS + API_ROUTE_POLICIES + PolicyEngine` |

Regla: `write_report=false` es el valor por defecto. `write_report=true` solo puede escribir evidencia regenerable bajo `outputs/reports/operator_dashboard_snapshot.json` y `.md`.

## POST-H-016-D — Portfolio status API mapping

POST-H-016-D agregó la ruta local/read-only de portfolio status mediante `ApplicationService`, sin selección activa de workspace, sin escritura cruzada y con `PolicyEngine`/token local.

| API ID | Método | Path | Operation | Domain service | Side effect | Auth | Policy/gate |
|---|---|---|---|---|---|---|---|
| `API-PORTFOLIO-STATUS` | `GET` | `/api/v1/portfolio/status` | `portfolio.status` | `PortfolioApplicationService` | `read_only` | `local-token-required` | `Policy/gate: token + CORS + API_ROUTE_POLICIES + PolicyEngine; no workspace switch; no connector write` |

## POST-H-028-A — Mapping protegido contra drift

Las rutas respaldadas por ApplicationService deben declarar `response_contract=ApplicationResponse` en el registro de rutas. POST-H-028-A bloquea rutas nuevas o stale que rompan este mapping.



## POST-H-028-B — Local auth and CORS hardening

`LocalApiSecurityHardeningRunner` valida la postura local de autenticacion y CORS: rutas protegidas requieren token, token invalido bloquea, token valido pasa, CORS no acepta wildcard, origen no local no recibe `Access-Control-Allow-Origin`, bind no local queda bloqueado, headers de seguridad se aplican y settings/providers no expone secretos raw.

## POST-H-028-C — Mapping visual hacia API local

El smoke visual verifica que Dashboard, Reports, Traces, Approvals, Settings y Operator Dashboard consuman solamente rutas permitidas por `UiRouteContractRegistry` y respaldadas por `ApiRouteContractRegistry`. No introduce nuevas operaciones de ApplicationService; solo agrega evidencia de renderabilidad y estados visuales mínimos.


## POST-H-028-D — Operator flows mapping

`OperatorFlowSmokeRunner` comprueba que la UI consuma ApplicationService/API para flujos de operador sin leer filesystem desde frontend y sin duplicar logica core. La cobertura es `implemented-initial` y prepara POST-H-028-E para enforcement del UI route registry.


## POST-H-028-E — UI route registry enforcement

POST-H-028-E agrega enforcement bloqueante del `UiRouteContractRegistry`. Las vistas criticas deben declarar sus fuentes, estados visuales y `allowed_api_routes`; esas rutas deben existir en `ApiRouteContractRegistry`. La UI conserva frontera API-only: no importa core Python, no lee `.devpilot/` ni `outputs/`, y no muestra controles para `patch/apply`, rollback execute, refactor execute, tests/run, git push o deploy.

El script `npm --prefix ui/web run test:route-enforcement` es dependency-light y complementa el CLI `python -m devpilot_core api ui-route-enforcement --json --write-report`.

## POST-H-031 — Operator evidence API mappings

POST-H-031 agrega vistas operacionales read-only/redacted mediante `ApplicationService`. Estas rutas no habilitan ejecución remota, connector write, plugin execution ni mutaciones destructivas. Todas quedan protegidas por token local, CORS restringido, `API_ROUTE_POLICIES` y `PolicyEngine`.

| API ID | Método | Path | Operation | Domain service | Side effect | Auth | Policy/gate |
|---|---|---|---|---|---|---|---|
| `api.operator.health` | `GET` | `/api/v1/operator/health` | `operator.health` | `ApplicationService.operator_health_summary` | `read_only` | `local-token-required` | `Policy/gate: token + CORS + API_ROUTE_POLICIES + PolicyEngine` |
| `api.operator.gaps` | `GET` | `/api/v1/operator/gaps` | `operator.gaps` | `ApplicationService.gap_action_map` | `read_only` | `local-token-required` | `Policy/gate: token + CORS + API_ROUTE_POLICIES + PolicyEngine; advisory actions only` |
| `api.operator.claims_no_go` | `GET` | `/api/v1/operator/claims-no-go` | `operator.claims_no_go` | `ApplicationService.claims_no_go_dashboard` | `read_only` | `local-token-required` | `Policy/gate: token + CORS + API_ROUTE_POLICIES + PolicyEngine; claims/no-go gates are not mutated` |
| `api.operator.evidence_export` | `GET` | `/api/v1/operator/evidence-export` | `operator.evidence_export` | `ApplicationService.operator_evidence_export` | `outputs-only on explicit write_report` | `local-token-required` | `Policy/gate: token + CORS + API_ROUTE_POLICIES + PolicyEngine; redacted export only; no patch execution; no raw payload export` |

Regla: `operator.evidence_export` requiere export redactado y opera en `dry_run` por defecto. Cuando se solicita escritura explícita, solo escribe paquete regenerable bajo `outputs/audit_exports/operator_evidence_export/`; nunca escribe fuente versionada ni expone `.env`, `.devpilot/devpilot.db`, prompts crudos u outputs crudos.

## UOC-001 — Workspace Documents read-only mapping

UOC-001 amplía la superficie ApplicationService/API con tres operaciones
estrictamente read-only. El root del workspace se resuelve en el servidor desde
el contexto registrado; el navegador solo utiliza identificadores opacos.

| API ID | Método | Path | Operation | Domain service | Side effect | Auth | Policy/gate |
|---|---|---|---|---|---|---|---|
| `API-WORKSPACE-DOCUMENTS-LIST` | `GET` | `/api/v1/workspace/documents` | `workspace.documents.list` | `WorkspaceDocumentsApplicationService` | `none` | `local-token-required` | `Policy/gate: token + CORS + API_ROUTE_POLICIES + PolicyEngine + active workspace + PathGuard + bounded no-follow discovery` |
| `API-WORKSPACE-DOCUMENTS-READ` | `GET` | `/api/v1/workspace/documents/{document_id}` | `workspace.documents.read` | `WorkspaceDocumentsApplicationService` | `none` | `local-token-required` | `Policy/gate: opaque id + active workspace + PathGuard + no-follow safe open + size/encoding allowlist` |
| `API-WORKSPACE-DOCUMENTS-METADATA` | `GET` | `/api/v1/workspace/documents/{document_id}/metadata` | `workspace.documents.metadata` | `WorkspaceDocumentsApplicationService` | `none` | `local-token-required` | `Policy/gate: opaque id + active workspace + PathGuard + bounded metadata/hash read` |

No existe operación de escritura documental, shell, ejecución remota, connector
write, plugin execution ni API externa en UOC-001.

## UOC-002 — Metadata, Git history y búsqueda documental mapping

UOC-002 añade cuatro operaciones estrictamente read-only sobre los IDs opacos
de UOC-001. Git se invoca únicamente mediante `GitAdapter` tipado y la búsqueda
no persiste contenido fuera de la memoria del proceso.

| API ID | Método | Path | Operation | Domain service | Side effect | Auth | Policy/gate |
|---|---|---|---|---|---|---|---|
| `API-WORKSPACE-DOCUMENTS-HISTORY` (`api.workspace.documents.history`) | `GET` | `/api/v1/workspace/documents/{document_id}/history` | `workspace.documents.history` | `WorkspaceDocumentInspectionApplicationService` | `none` | `local-token-required` | opaque ID + active workspace + typed GitAdapter + bounded pagination |
| `API-WORKSPACE-DOCUMENTS-DIFF` (`api.workspace.documents.diff`) | `GET` | `/api/v1/workspace/documents/{document_id}/diff` | `workspace.documents.diff` | `WorkspaceDocumentInspectionApplicationService` | `none` | `local-token-required` | validated HEAD/SHA ref + bounded diff bytes + explicit truncation |
| `API-WORKSPACE-DOCUMENTS-SEARCH` (`api.workspace.documents.search`) | `GET` | `/api/v1/workspace/documents/search` | `workspace.documents.search` | `WorkspaceDocumentInspectionApplicationService` | `memory-only cache` | `local-token-required` | workspace-isolated index + bounded query/results + UOC-001 exclusions |
| `API-WORKSPACE-DOCUMENTS-LINKS` (`api.workspace.documents.links`) | `GET` | `/api/v1/workspace/documents/{document_id}/links` | `workspace.documents.links` | `WorkspaceDocumentInspectionApplicationService` | `none` | `local-token-required` | opaque ID + in-root Markdown link resolution + no absolute/ADS escape |

No se habilitan escritura documental, comandos Git libres, shell, red externa,
connector write, plugin execution ni ejecución remota.


## UOC-003 — Workspace validation and traceability

| API route | Application operation | Mutation boundary | Evidence |
|---|---|---|---|
| `POST /api/v1/workspace/validations/plan` | `workspace.validations.plan` | none | immutable in-memory plan |
| `POST /api/v1/workspace/validations/execute` | `workspace.validations.execute` | runtime evidence only | bounded report and trace under active workspace |
| `GET /api/v1/workspace/validations/{job_id}` | `workspace.validations.status` | none | reads opaque validation job |
| `GET /api/v1/workspace/traceability` | `workspace.traceability` | none | explicit-only navigable matrix |

The facade reuses deterministic validators and never executes free-form shell or CLI text. Source documents remain read-only. The first UOC-003 job implementation is synchronous and preliminary; async queueing, heartbeat and cancellation remain assigned to UOC-007/UOC-008.


## UOC-004 — Workspace edit planning

| Route | Application operation | Mutation |
|---|---|---|
| `POST /api/v1/workspace/edit-plans/plan` | `workspace.edits.plan` | none / plan-only |
| `GET /api/v1/workspace/edit-plans/{plan_id}` | `workspace.edits.status` | none |
| `POST /api/v1/workspace/edit-plans/{plan_id}/recheck` | `workspace.edits.recheck` | none |

UOC-004 does not expose apply, filesystem write, Git stage or shell.


## UOC-003/UOC-004 synchronized plan/read routes

| API id | Route | Application operation | Application Service | Policy/gate | Side effect |
|---|---|---|---|---|---|
| `API-UOC003-VALIDATION-PLAN` | `POST /api/v1/workspace/validations/plan` | `workspace.validations.plan` | `ApplicationService.workspace_validations_plan` | Policy/gate: token + local policy | none |
| `API-UOC003-VALIDATION-EXECUTE` | `POST /api/v1/workspace/validations/execute` | `workspace.validations.execute` | `ApplicationService.workspace_validations_execute` | Policy/gate: token + local policy | runtime evidence only |
| `API-UOC003-VALIDATION-STATUS` | `GET /api/v1/workspace/validations/{job_id}` | `workspace.validations.status` | `ApplicationService.workspace_validations_status` | Policy/gate: token + local policy | none |
| `API-UOC003-TRACEABILITY` | `GET /api/v1/workspace/traceability` | `workspace.traceability` | `ApplicationService.workspace_traceability` | Policy/gate: token + local policy | none |
| `API-UOC004-EDIT-PLAN` | `POST /api/v1/workspace/edit-plans/plan` | `workspace.edits.plan` | `ApplicationService.workspace_edit_plan` | Policy/gate: token + PathGuard/SecretGuard + base SHA | plan-only |
| `API-UOC004-EDIT-PLAN-STATUS` | `GET /api/v1/workspace/edit-plans/{plan_id}` | `workspace.edits.status` | `ApplicationService.workspace_edit_plan_status` | Policy/gate: token + opaque plan id | none |
| `API-UOC004-EDIT-PLAN-RECHECK` | `POST /api/v1/workspace/edit-plans/{plan_id}/recheck` | `workspace.edits.recheck` | `ApplicationService.workspace_edit_plan_recheck` | Policy/gate: token + immutable plan hash + optimistic concurrency | none |

UOC-004 is plan-only: no patch execution, filesystem write, stage or commit.

## UOC-005 — approval-bound document apply/rollback

| API id | API route | Application operation | Application Service | Mutation boundary | Approval/policy |
|---|---|---|---|---|---|
| `API-UOC005-EDIT-APPLY-APPROVAL` | `POST /api/v1/workspace/edit-plans/{plan_id}/approval-request` | `workspace.edits.approval_request` | `ApplicationService.workspace_edit_apply_approval_request` | Local approval state only | Policy/gate: binds exact plan/hash/base/actor/scope/TTL; source unchanged |
| `API-UOC005-EDIT-APPLY` | `POST /api/v1/workspace/edit-plans/{plan_id}/apply` | `workspace.edits.apply` | `ApplicationService.workspace_edit_apply` | Approval-gated atomic document source write | Policy/gate: exact approved binding + recheck + verified external backup + post-validation |
| `API-UOC005-EDIT-EXECUTION-STATUS` | `GET /api/v1/workspace/edit-executions/{execution_id}` | `workspace.edits.execution_status` | `ApplicationService.workspace_edit_execution_status` | none | Policy/gate: protected opaque-id read; backup ref remains relative |
| `API-UOC005-EDIT-ROLLBACK-APPROVAL` | `POST /api/v1/workspace/edit-executions/{execution_id}/rollback-approval-request` | `workspace.edits.rollback_approval_request` | `ApplicationService.workspace_edit_rollback_approval_request` | Local approval state only | Policy/gate: new exact rollback binding; source unchanged |
| `API-UOC005-EDIT-ROLLBACK` | `POST /api/v1/workspace/edit-executions/{execution_id}/rollback` | `workspace.edits.rollback` | `ApplicationService.workspace_edit_rollback` | Approval-gated bounded pre-commit source restore | Policy/gate: exact approval + post-hash + Git unstaged + verified backup |

Transport middleware continues to enforce token/local policy. The request-specific sensitive action is enforced inside `WorkspaceEditExecutionApplicationService`, where the immutable plan/execution hash and approval id are available for StrongApprovalBinding. Generic patch/rollback executors and Git mutation remain disabled.

## UOC-006 — Governed Git operations

All UOC-006 routes remain local-only and typed; no browser-provided Git command string is accepted. Policy/gate includes local token, explicit API route policy and the WorkspaceGitOperationsApplicationService.

| API ID | Method / path | Application operation | Policy/gate |
|---|---|---|---|
| `API-UOC006-STATUS` | `GET /api/v1/workspace/git/status` | `workspace.git.status` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-HISTORY` | `GET /api/v1/workspace/git/history` | `workspace.git.history` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-COMPARE` | `GET /api/v1/workspace/git/compare` | `workspace.git.compare` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-PLANS-CREATE` | `POST /api/v1/workspace/git/plans` | `workspace.git.plan` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-PLANS-READ` | `GET /api/v1/workspace/git/plans/{plan_id}` | `workspace.git.plan_status` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-STAGE-APPROVAL` | `POST /api/v1/workspace/git/plans/{plan_id}/stage-approval-request` | `workspace.git.stage_approval_request` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-STAGE` | `POST /api/v1/workspace/git/plans/{plan_id}/stage` | `workspace.git.stage` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-EXECUTIONS-READ` | `GET /api/v1/workspace/git/executions/{execution_id}` | `workspace.git.execution_status` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-COMMIT-APPROVAL` | `POST /api/v1/workspace/git/stage-executions/{execution_id}/commit-approval-request` | `workspace.git.commit_approval_request` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-COMMIT` | `POST /api/v1/workspace/git/stage-executions/{execution_id}/commit` | `workspace.git.commit` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-BRANCH-PLAN` | `POST /api/v1/workspace/git/branches/plan` | `workspace.git.branch_plan` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-BRANCH-APPROVAL` | `POST /api/v1/workspace/git/branches/{plan_id}/approval-request` | `workspace.git.branch_approval_request` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |
| `API-UOC006-BRANCH-CREATE` | `POST /api/v1/workspace/git/branches/{plan_id}/create` | `workspace.git.branch_create` | Policy/gate: local token + route policy + typed UOC-006 service; arbitrary Git args/network/destructive commands blocked. |


## UOC-008 — Job Console and operational observability

UOC-008 exposes local governed-job observation/control only. It does **not** enable generic capability execution, browser shell text, remote execution, connector write or plugin execution. Runtime mutations are limited to bounded job lifecycle state, retry metadata and process-tree cancellation of a worker PID recorded by the trusted runtime.

| API ID | Method / path | Application operation | Application Service | Policy/gate |
|---|---|---|---|---|
| `API-UOC008-JOBS-LIST` | `GET /api/v1/jobs` | `jobs.list` | `ApplicationService.jobs_list` | Policy/gate: local token + restricted CORS + typed ApplicationService + bounded filters/pagination. |
| `API-UOC008-JOBS-INSPECT` | `GET /api/v1/jobs/{job_id}` | `jobs.inspect` | `ApplicationService.jobs_inspect` | Policy/gate: opaque job id + local token; internal integrity hashes are removed from browser projection. |
| `API-UOC008-JOBS-LOGS` | `GET /api/v1/jobs/{job_id}/logs` | `jobs.logs` | `ApplicationService.jobs_logs` | Policy/gate: opaque job id + bounded cursor/page + backend redaction + per-job size limit. |
| `API-UOC008-JOBS-CANCEL` | `POST /api/v1/jobs/{job_id}/cancel` | `jobs.cancel` | `ApplicationService.jobs_cancel` | Policy/gate: local token + protected job-control policy + lifecycle validation + fixed-argv process-tree termination only for recorded worker PID. |
| `API-UOC008-JOBS-RETRY` | `POST /api/v1/jobs/{job_id}/retry` | `jobs.retry` | `ApplicationService.jobs_retry` | Policy/gate: local token + protected job-control policy + terminal-state/retry-budget validation; creates a fresh governed job and never autoexecutes it. |

Startup calls `ApplicationService.jobs_reconcile` to adjudicate stale/orphan active jobs after restart. Trusted runtime workers can call `jobs_record_progress` internally to update phase/progress and heartbeat; no browser endpoint can inject a PID or arbitrary command.


## UOC-009 — Quality, tests y release operations

UOC-009 adds six typed local API routes. The UI never supplies shell text, executable paths or free pytest arguments; all execution is selected by `operation_id`, capability registry, Test Contract Registry IDs and policy/approval contracts.

| HTTP | Route | Application operation | Boundary |
|---|---|---|---|
| GET | `/api/v1/quality/operations` | `quality.operations` | typed operation/profile catalog |
| GET | `/api/v1/quality/baseline` | `quality.baseline` | Project State + manifests/baseline inspection |
| POST | `/api/v1/quality/test-impact/plan` | `quality.test_impact_plan` | deterministic Test Impact v2 |
| POST | `/api/v1/quality/jobs/plan` | `quality.jobs.plan` | governed plan + budget/approval binding |
| POST | `/api/v1/quality/jobs/{job_id}/execute` | `quality.jobs.execute` | fixed typed worker, `shell=False` |
| POST | `/api/v1/quality/evidence/package` | `quality.evidence_package` | bounded local evidence export |

Full regression remains a separate sensitive operation: it requires explicit approval plus the exact confirmation phrase and is never started automatically after focused tests.

UOC-009 API contract identifiers: `API-UOC009-QUALITY-OPERATIONS`, `API-UOC009-QUALITY-BASELINE`, `API-UOC009-QUALITY-TEST-IMPACT-PLAN`, `API-UOC009-QUALITY-JOBS-PLAN`, `API-UOC009-QUALITY-JOBS-EXECUTE`, `API-UOC009-QUALITY-EVIDENCE-PACKAGE`.


## UOC-010 — RAG, agents, tools and handoffs

UOC-010 exposes exactly six typed local API routes. Browser input selects registered operation/provider/agent/workflow identifiers only; no command text, arbitrary tool, remote execution, connector write, plugin execution or external API is enabled.

| API ID | Method / path | Application operation | Application Service | Policy/gate |
|---|---|---|---|---|
| `API-UOC010-AI-OPERATIONS` | `GET /api/v1/ai/operations` | `ai.operations` | `ApplicationService.ai_operations` | Policy/gate: local token + typed UOC-010 registry. |
| `API-UOC010-AI-STATUS` | `GET /api/v1/ai/status` | `ai.status` | `ApplicationService.ai_status` | Policy/gate: provider/RAG/tool/memory/handoff status only. |
| `API-UOC010-AI-JOBS-PLAN` | `POST /api/v1/ai/jobs/plan` | `ai.jobs.plan` | `ApplicationService.ai_jobs_plan` | Policy/gate: registered operation + provider/tool allowlist + budgets + approval binding when required. |
| `API-UOC010-AI-JOBS-EXECUTE` | `POST /api/v1/ai/jobs/{job_id}/execute` | `ai.jobs.execute` | `ApplicationService.ai_jobs_execute` | Policy/gate: fixed typed worker, `shell=False`, mock/local only. |
| `API-UOC010-AI-JOBS-RESULT` | `GET /api/v1/ai/jobs/{job_id}/result` | `ai.jobs.result` | `ApplicationService.ai_jobs_result` | Policy/gate: bounded local result projection with citations/provider/cost visibility. |
| `API-UOC010-AI-EVIDENCE-PACKAGE` | `POST /api/v1/ai/evidence/package` | `ai.evidence_package` | `ApplicationService.ai_evidence_package` | Policy/gate: bounded local evidence export; memory is excluded as formal evidence. |


## DEVPL-GSDLC-01-E successor route

| Endpoint | Operation | Service mapping | Control |
|---|---|---|---|
| `GET /api/v1/guided-sdlc/status` | `guided_sdlc.project_status` / `API-GSDLC-01-E-PROJECT-STATUS` | `ApplicationService.guided_sdlc_project_status_primary` → `GuidedSDLCApplicationService.project_status_primary` → `GuidedSDLCService` / `ProjectProgressEngine` | Policy/gate: local token required; actor-neutral read-only DTO; no source/Git/state mutation; no direct UI filesystem access. |
