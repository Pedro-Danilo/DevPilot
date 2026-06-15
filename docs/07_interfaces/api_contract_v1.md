---
title: "DevPilot Local — API Contract v1 preliminar"
doc_id: "DEVPL-INTERFACE-API-CONTRACT-V1"
status: "approved"
approval: "approved_after_func_sprint_68_api_security"
version: "1.2.0-secured-initial"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-68"
updated: "2026-06-15"
source_application_contract: "DevPilotApplicationServiceContract 2.0"
source_repo: "repo_DevPilot_Local_84.zip"
api_status: "secured-initial"
server_implemented: true
token_required: true
cors_restricted: true
policy_binding_enabled: true
ui_implemented: false
desktop_deferred: true
---

# DevPilot Local — API Contract v1 preliminar

## Estado

`approved` / `secured-initial` para `FUNC-SPRINT-68`.

Este contrato define la API local v1 de DevPilot. Desde `FUNC-SPRINT-67` existe un adapter FastAPI local y desde `FUNC-SPRINT-68` la API queda endurecida con token local, CORS restringido, headers de seguridad y binding con `PolicyEngine` para rutas protegidas. Sigue siendo un MVP local: no implementa RBAC enterprise, multiusuario, sesiones web, TLS productivo ni exposición pública.

## Propósito

Formalizar la frontera `API local → ApplicationService → DevPilot Core` para que los sprints posteriores puedan implementar Web UI local sin duplicar lógica de negocio ni saltarse `PolicyEngine`, MIASI, ReportEngine, LocalStore, AgentOps o los contratos `CommandResult`/`ApplicationResponse`.

## Alcance

Incluye:

- namespace `/api/v1`;
- endpoints de workspace, validation, MIASI, repo, review, refactor, model, observability, history, standards y application contract;
- request envelope basado en `ApplicationRequest`;
- response envelope basado en `ApplicationResponse`, que preserva `CommandResult`;
- errores normalizados `400`, `401`, `403`, `422` y `500` como `ApplicationResponse`;
- mapping obligatorio endpoint → operation → domain service;
- OpenAPI estático en `docs/07_interfaces/openapi_v1.json`;
- servidor FastAPI local MVP en `src/devpilot_core/interfaces/api`;
- token local por header `X-DevPilot-Token` o `Authorization: Bearer <token>`;
- CORS restringido a origins locales permitidos;
- headers mínimos de seguridad;
- policy binding para rutas protegidas.

No incluye:

- Web UI;
- Desktop shell;
- RBAC industrial;
- login multiusuario;
- cookies de sesión;
- exposición pública;
- ejecución remota.

## Modelo de integración

```text
Web UI local futura
  → API local /api/v1 secured-initial
    → token/CORS/security headers/policy binding
      → ApplicationService.handle(ApplicationRequest)
        → DomainService
          → DevPilot Core
            → CommandResult
              → ApplicationResponse
```

## Reglas vinculantes

1. Toda ruta debe empezar por `/api/v1`.
2. Toda ruta protegida debe exigir token local.
3. Los únicos endpoints públicos mínimos son `/api/v1/health`, `/api/v1/docs` y `/api/v1/openapi.json`.
4. CORS wildcard queda prohibido por defecto.
5. Toda ruta protegida debe tener binding con `PolicyEngine` mediante `API_ROUTE_POLICIES`.
6. Toda respuesta, incluso errores de seguridad, debe preservar `ApplicationResponse`.
7. Los endpoints `POST` son read-only/dry-run o plan-only; no autorizan escritura ni ejecución crítica.
8. Las operaciones write/execute futuras deben requerir `PolicyEngine` y Approval Workflow.
9. La API local debe escuchar por defecto en `127.0.0.1`.
10. La Web UI no podrá leer filesystem directamente ni importar módulos Python del core.

## Endpoints v1 preliminares

| API ID | Método | Path | Operation | Domain service | Side effect | Auth | Policy/gate |
|---|---|---|---|---|---|---|---|
| `API-WORKSPACE-STATUS` | `GET` | `/api/v1/workspace/status` | `workspace.status` | `WorkspaceApplicationService.status` | `none` | `local-token-required` | `PolicyEngine read allow` |
| `API-VALIDATION-FRONTMATTER` | `POST` | `/api/v1/validation/frontmatter` | `validation.frontmatter` | `ValidationApplicationService.validate_frontmatter` | `none` | `local-token-required` | `PolicyEngine + PathGuard lower layer` |
| `API-VALIDATION-ARTIFACT` | `POST` | `/api/v1/validation/artifact` | `validation.artifact` | `ValidationApplicationService.validate_artifact` | `none` | `local-token-required` | `PolicyEngine + PathGuard lower layer` |
| `API-VALIDATION-READINESS` | `POST` | `/api/v1/validation/readiness` | `validation.readiness` | `ValidationApplicationService.readiness` | `report_when_adapter_requests_it` | `local-token-required` | `PolicyEngine read allow; reports explicit` |
| `API-MIASI-STATUS` | `GET` | `/api/v1/miasi/status` | `miasi.validate` | `MiasiApplicationService.validate` | `none` | `local-token-required` | `PolicyEngine read allow` |
| `API-REPO-INVENTORY` | `GET` | `/api/v1/repo/inventory` | `repo.inventory` | `RepoApplicationService.inventory` | `none` | `local-token-required` | `PolicyEngine read allow; Git read-only` |
| `API-REVIEW-CODE` | `POST` | `/api/v1/review/code` | `review.code` | `ReviewApplicationService.code_review` | `none` | `local-token-required` | `PolicyEngine read allow; dry-run only` |
| `API-REFACTOR-PLAN` | `POST` | `/api/v1/refactor/plan` | `refactor.plan` | `RefactorApplicationService.plan` | `none` | `local-token-required` | `PolicyEngine read allow; plan-only; no patch execution` |
| `API-MODEL-PROVIDERS` | `GET` | `/api/v1/model/providers` | `model.providers` | `ModelApplicationService.providers` | `none` | `local-token-required` | `PolicyEngine read allow; no external API` |
| `API-OBSERVABILITY-TRACES` | `GET` | `/api/v1/observability/traces` | `observability.trace_report` | `ObservabilityApplicationService.trace_report` | `none` | `local-token-required` | `PolicyEngine read allow; bounded read` |
| `API-OBSERVABILITY-METRICS` | `GET` | `/api/v1/observability/metrics` | `observability.metrics_summary` | `ObservabilityApplicationService.metrics_summary` | `none` | `local-token-required` | `PolicyEngine read allow; bounded read` |
| `API-HISTORY-RUNS` | `GET` | `/api/v1/history/runs` | `history.runs` | `HistoryApplicationService.list_runs` | `none` | `local-token-required` | `PolicyEngine read allow; bounded LocalStore read` |
| `API-APPLICATION-CONTRACT` | `GET` | `/api/v1/application/contract` | `app.contract` | `ApplicationService.application_contract` | `none` | `local-token-required` | `PolicyEngine read allow` |
| `API-STANDARDS-STATUS` | `GET` | `/api/v1/standards/status` | `standards.status` | `ValidationApplicationService.standards_status` | `none` | `local-token-required` | `PolicyEngine read allow` |

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

| Código HTTP | Uso | Contrato |
|---|---|---|
| `400` | Request inválido o parámetro no soportado | `ApplicationResponse` con finding `fail` o `error`. |
| `401` | Token ausente o inválido | `ApplicationResponse` con finding `API_TOKEN_MISSING_BLOCK` o `API_TOKEN_INVALID_BLOCK`. |
| `403` | Bloqueo de policy, aprobación o seguridad | `ApplicationResponse` con finding `block`. |
| `422` | Violación de contrato/schema | `ApplicationResponse` con finding estructural. |
| `500` | Error interno controlado | `ApplicationResponse` sin secretos ni stdout/stderr crudos. |

## Seguridad prevista

Sprint 68 implementa controles mínimos ejecutables:

- token local temporal en memoria;
- token generado con `python -m devpilot_core api token --json`;
- token leído desde `DEVPILOT_API_TOKEN` para ejecución real;
- headers `X-DevPilot-Token` o `Authorization: Bearer <token>`;
- CORS allowlist local sin wildcard;
- security headers mínimos;
- policy binding por ruta protegida;
- bloqueo de host remoto desde CLI.

Estos controles son suficientes para la Web UI local MVP, pero no equivalen a seguridad enterprise.

## Criterios PASS

- Existe contrato API v1 sincronizado con servidor y seguridad local.
- OpenAPI estático define `/api/v1` y `LocalTokenAuth`.
- Cada endpoint tiene `x-devpilot-operation` y mapping a `ApplicationService`.
- Errores usan `ApplicationResponse`.
- Token es requerido para endpoints no públicos.
- CORS wildcard está deshabilitado por defecto.
- Rutas protegidas tienen policy binding.

## Criterios BLOCK

- Endpoint sin mapping a `ApplicationService`.
- Ruta fuera de `/api/v1`.
- Respuestas que no preserven `ApplicationResponse`.
- Definición de acción write/execute sin approval.
- Cualquier host default distinto de `127.0.0.1`.
- CORS wildcard por defecto.
- Token crudo persistido en logs/reportes.
- Cualquier reactivación de Desktop como alcance de Fase F.

## Riesgos

| ID | Riesgo | Mitigación |
|---|---|---|
| `RISK-FUNC-68-001` | Token local visto por procesos del mismo usuario | Aceptado para MVP local; no persistir token y documentar límite. |
| `RISK-FUNC-68-002` | CORS mal configurado | Tests específicos verifican no wildcard. |
| `RISK-FUNC-68-003` | Falsa seguridad | Documento declara que no hay RBAC enterprise ni Web real pública. |
| `RISK-FUNC-68-004` | Policy binding incompleto | `tests/test_api_security.py` valida cobertura de rutas protegidas. |
