---
title: "DevPilot Local — API v1 service mapping"
doc_id: "DEVPL-INTERFACE-API-SERVICE-MAPPING-V1"
status: "approved"
approval: "approved_after_func_sprint_68_api_security"
version: "1.2.0-secured-initial"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-68"
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
