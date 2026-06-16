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
