---
title: "DevPilot Local — API Contract v1 preliminar"
doc_id: "DEVPL-INTERFACE-API-CONTRACT-V1"
status: "approved"
approval: "approved_after_func_sprint_67_api_local_mvp"
version: "1.1.0-implemented-initial"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-67"
updated: "2026-06-15"
source_application_contract: "DevPilotApplicationServiceContract 2.0"
source_repo: "repo_DevPilot_Local_81.zip"
api_status: "implemented-initial"
server_implemented: true
ui_implemented: false
desktop_deferred: true
---

# DevPilot Local — API Contract v1 preliminar

## Estado

`approved` / `implemented-initial` para `FUNC-SPRINT-67`.

Este documento define el contrato API local v1 de DevPilot y queda sincronizado con el servidor FastAPI local MVP implementado en `FUNC-SPRINT-67`. El contrato sigue siendo preliminar en seguridad: la API ya existe como adapter local read-only/dry-run sobre `ApplicationService v2`, pero token local, CORS restringido y policy binding ejecutable quedan diferidos explícitamente a `FUNC-SPRINT-68`.

## Propósito

Formalizar la frontera `API local → ApplicationService → DevPilot Core` para que los sprints posteriores puedan implementar servidor local y Web UI sin duplicar lógica de negocio ni saltarse `PolicyEngine`, MIASI, ReportEngine, LocalStore, AgentOps o los contratos `CommandResult`/`ApplicationResponse`.

## Alcance

Incluye:

- namespace `/api/v1`;
- endpoints preliminares de workspace, validation, MIASI, repo, review, refactor, model, observability, history y application contract;
- request envelope basado en `ApplicationRequest`;
- response envelope basado en `ApplicationResponse`, que preserva `CommandResult`;
- errores normalizados `400`, `403`, `422` y `500` como `ApplicationResponse`;
- mapping obligatorio endpoint → operation → domain service;
- OpenAPI estático en `docs/07_interfaces/openapi_v1.json`;
- servidor FastAPI local MVP en `src/devpilot_core/interfaces/api`;
- comando CLI `python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json`.

No incluye:

- token real;
- CORS real;
- frontend;
- Desktop shell;
- auth/RBAC;
- ejecución remota;
- exposición pública.

## Modelo de integración

```text
Web UI local futura
  → API local /api/v1 implementada-inicial
    → ApplicationService.handle(ApplicationRequest)
      → DomainService
        → DevPilot Core
          → CommandResult
            → ApplicationResponse
```

## Reglas vinculantes

1. Toda ruta debe empezar por `/api/v1`.
2. Toda ruta debe mapear a una operación expuesta por `ApplicationService.application_contract()`, salvo `/api/v1/application/contract`, que expone el contrato de bootstrap.
3. Toda respuesta, incluso errores, debe preservar `ApplicationResponse`.
4. Los endpoints `POST` de Sprint 66 son contratos para operaciones read-only/dry-run o plan-only; no autorizan escritura ni ejecución crítica.
5. Las operaciones write/execute futuras deben requerir `PolicyEngine` y Approval Workflow.
6. La API local futura debe escuchar por defecto en `127.0.0.1`.
7. CORS wildcard queda prohibido por defecto.
8. Token local queda planificado para Sprint 68; Sprint 67 no lo implementa por alcance controlado.
9. La Web UI no podrá leer filesystem directamente ni importar módulos Python del core.

## Endpoints v1 preliminares

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

## Request envelope

Los endpoints `POST` usan `ApplicationRequest`:

```json
{
  "operation": "validation.artifact",
  "payload": {"path": "docs/05_operations/runbook.md", "strict": false},
  "client": "api-local",
  "dry_run": true
}
```

Los endpoints `GET` no ejecutan mutaciones y podrán aceptar parámetros acotados como `limit` en historia/observabilidad cuando aplique.

## Response envelope

Todas las respuestas deben ser adaptaciones de `ApplicationResponse`:

```json
{
  "contract": "DevPilotApplicationResponse",
  "schema_version": "1.0",
  "operation": "workspace.status",
  "ok": true,
  "exit_code": 0,
  "message": "Workspace status passed.",
  "data": {},
  "findings": [],
  "generated_at": "2026-06-15T00:00:00Z"
}
```

## Errores

| Código HTTP futuro | Uso | Contrato |
|---|---|---|
| `400` | Request inválido o parámetro no soportado | `ApplicationResponse` con finding `fail` o `error`. |
| `403` | Bloqueo de policy, aprobación o seguridad | `ApplicationResponse` con finding `block`. |
| `422` | Violación de contrato/schema | `ApplicationResponse` con finding estructural. |
| `500` | Error interno controlado | `ApplicationResponse` sin secretos ni stdout/stderr crudos. |

## Seguridad prevista

Sprint 67 implementa la API local MVP read-only/dry-run. Los controles ejecutables de seguridad HTTP quedan en sprints posteriores:

- Sprint 68: token local, CORS restringido, headers y policy binding.

Criterios mínimos ya fijados:

- default host futuro: `127.0.0.1`;
- no `0.0.0.0` por defecto;
- no CORS wildcard;
- no secretos en responses;
- no prompts/completions crudos;
- reportes/trazas con límites;
- operaciones críticas bloqueadas sin Approval.

## Criterios PASS

- Existe contrato API v1 antes de servidor.
- OpenAPI estático define `/api/v1`.
- Cada endpoint tiene `x-devpilot-operation` y mapping a `ApplicationService`.
- Errores usan `ApplicationResponse`.
- Dependencias FastAPI/uvicorn/httpx quedan declaradas en extras `api` y `dev`.
- Se implementa servidor local MVP, sin frontend.

## Criterios BLOCK

- Endpoint sin mapping a `ApplicationService`.
- Ruta fuera de `/api/v1`.
- Respuestas que no preserven `ApplicationResponse`.
- Definición de acción write/execute sin approval.
- Cualquier host default distinto de `127.0.0.1`.
- Cualquier reactivación de Desktop como alcance de Fase F.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| `RISK-FUNC-66-001` | Contrato diverge de `ApplicationService` | `tests/test_api_contract.py` compara OpenAPI contra app contract. |
| `RISK-FUNC-66-002` | Endpoints demasiado amplios | Mantener MVP read-only/dry-run/plan-only. |
| `RISK-FUNC-66-003` | Seguridad postergada se interpreta como ausente | Documentar token/CORS/policy binding como Sprint 68 obligatorio. |
| `RISK-FUNC-66-004` | UI futura lee filesystem directo | Mapping obliga UI→API→ApplicationService. |
