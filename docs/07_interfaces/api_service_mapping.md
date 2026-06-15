---
title: "DevPilot Local — API v1 service mapping"
doc_id: "DEVPL-INTERFACE-API-SERVICE-MAPPING-V1"
status: "approved"
approval: "approved_after_func_sprint_67_api_local_mvp"
version: "1.1.0-implemented-initial"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-67"
updated: "2026-06-15"
source_contract: "docs/07_interfaces/api_contract_v1.md"
source_openapi: "docs/07_interfaces/openapi_v1.json"
server_implemented: true
---

# DevPilot Local — API v1 service mapping

## Estado

`approved` / `implemented-initial` para `FUNC-SPRINT-67`.

## Propósito

Garantizar trazabilidad explícita entre cada endpoint preliminar `/api/v1`, la operación de `ApplicationService v2`, el servicio de dominio responsable, el comando CLI equivalente y los controles de seguridad esperados.

## Alcance

Este mapping ya está sincronizado con el servidor FastAPI local MVP. Su función sigue siendo bloquear dos riesgos: que la API importe motores internos directamente y que la Web UI futura duplique lógica del core.

## Matriz endpoint → ApplicationService

| API ID | Método | Path | Operation | Domain service | Side effect | Auth plan | Policy/gate |
|---|---|---|---|---|---|---|---|
| `API-WORKSPACE-STATUS` | `GET` | `/api/v1/workspace/status` | `workspace.status` | `WorkspaceApplicationService.status` | `none` | `public-local-read` | `None` |
| `API-VALIDATION-FRONTMATTER` | `POST` | `/api/v1/validation/frontmatter` | `validation.frontmatter` | `ValidationApplicationService.validate_frontmatter` | `none` | `token-planned-sprint-68` | `PathGuard on adapter` |
| `API-VALIDATION-ARTIFACT` | `POST` | `/api/v1/validation/artifact` | `validation.artifact` | `ValidationApplicationService.validate_artifact` | `none` | `token-planned-sprint-68` | `PathGuard on adapter` |
| `API-VALIDATION-READINESS` | `POST` | `/api/v1/validation/readiness` | `validation.readiness` | `ValidationApplicationService.readiness` | `report_when_adapter_requests_it` | `token-planned-sprint-68` | `Report writes explicit only` |
| `API-MIASI-STATUS` | `GET` | `/api/v1/miasi/status` | `miasi.validate` | `MiasiApplicationService.validate` | `none` | `public-local-read` | `MIASI registries read-only` |
| `API-REPO-INVENTORY` | `GET` | `/api/v1/repo/inventory` | `repo.inventory` | `RepoApplicationService.inventory` | `none` | `token-planned-sprint-68` | `Git read-only / PathGuard` |
| `API-REVIEW-CODE` | `POST` | `/api/v1/review/code` | `review.code` | `ReviewApplicationService.code_review` | `none` | `token-planned-sprint-68` | `CODE_REVIEW_DRY_RUN_ALLOW` |
| `API-REFACTOR-PLAN` | `POST` | `/api/v1/refactor/plan` | `refactor.plan` | `RefactorApplicationService.plan` | `none` | `token-planned-sprint-68` | `plan-only; no patch execution` |
| `API-MODEL-PROVIDERS` | `GET` | `/api/v1/model/providers` | `model.providers` | `ModelApplicationService.providers` | `none` | `token-planned-sprint-68` | `CostGuard/SecretGuard; no external API` |
| `API-OBSERVABILITY-TRACES` | `GET` | `/api/v1/observability/traces` | `observability.trace_report` | `ObservabilityApplicationService.trace_report` | `none` | `token-planned-sprint-68` | `bounded read; secret redaction` |
| `API-OBSERVABILITY-METRICS` | `GET` | `/api/v1/observability/metrics` | `observability.metrics_summary` | `ObservabilityApplicationService.metrics_summary` | `none` | `token-planned-sprint-68` | `bounded read; secret redaction` |
| `API-HISTORY-RUNS` | `GET` | `/api/v1/history/runs` | `history.runs` | `HistoryApplicationService.list_runs` | `none` | `token-planned-sprint-68` | `bounded LocalStore read` |
| `API-APPLICATION-CONTRACT` | `GET` | `/api/v1/application/contract` | `app.contract` | `ApplicationService.application_contract` | `none` | `public-local-read` | `None` |
| `API-STANDARDS-STATUS` | `GET` | `/api/v1/standards/status` | `standards.status` | `ValidationApplicationService.standards_status` | `none` | `public-local-read` | `DOC_VALIDATE_ALLOW` |

## Reglas de implementación vigente y futura

1. El handler HTTP debe construir un `ApplicationRequest`.
2. El handler debe llamar `ApplicationService.handle()` o un método de dominio expuesto formalmente.
3. El handler debe devolver `ApplicationResponse`.
4. El handler no debe importar directamente validators, repo analyzers, ReviewEngine, RefactorPlanner, ModelAdapterRouter, LocalStore ni TraceStore.
5. Acciones críticas siguen bloqueadas hasta contar con policy binding y Approval Workflow.

## Criterios PASS

- Cada path de `openapi_v1.json` aparece en esta matriz.
- Cada operation coincide con `ApplicationService.application_contract()`.
- Cada endpoint declara side effect y plan de seguridad.
- No hay rutas mutantes como patch apply, rollback execute o refactor execute.

## Criterios BLOCK

- Endpoint sin `operation`.
- Endpoint sin servicio de dominio.
- Endpoint que apunte a filesystem/UI directamente.
- Endpoint crítico sin Approval planificado.
