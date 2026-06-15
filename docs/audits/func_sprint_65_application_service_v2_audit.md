---
title: "Auditoría FUNC-SPRINT-65 — ApplicationService v2 por dominios"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-65"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-65"
updated: "2026-06-14"
source_repo: "repo_DevPilot_Local_79.zip"
source_backlog: "docs/devpilot_backlog_fase_F_producto_visual.md"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval: "approved_by_func_sprint_65"
---

# Auditoría FUNC-SPRINT-65 — ApplicationService v2 por dominios

## 0. Estado

Veredicto: `PASS`.

`FUNC-SPRINT-65` queda implementado como **implemented-initial**. El sprint amplía `ApplicationService` para cubrir dominios principales sin implementar API HTTP, Web UI, Desktop shell, CORS, token, auth ni dependencias externas.

## 1. Propósito

Auditar que DevPilot dispone de una frontera de aplicación suficientemente estable para que los próximos sprints de Fase F creen contratos API y API local sin duplicar lógica del core en la interfaz visual.

## 2. Alcance implementado

| Entregable | Estado | Comentario |
|---|---|---|
| ApplicationService v2 | Implementado | Fachada compuesta por dominios. |
| Domain services | Implementado | Workspace, validation, MIASI, evals, repo, review, refactor, model, history, observability. |
| ApplicationRequest dispatcher | Implementado | `ApplicationService.handle()` devuelve `ApplicationResponse`. |
| Contract v2 | Implementado | `schema_version=2.0`, capabilities/rutas contract-only. |
| CLI light delegation | Implementado inicial | Comandos representativos delegan en `ApplicationService`. |
| Pruebas v2 | Implementado | `tests/test_application_services_v2.py`. |
| Manifiesto Sprint 65 | Implementado | `docs/functional_sprint_65_manifest.json`. |

## 3. Funcionamiento técnico

La arquitectura queda:

```text
CLI / API local futura / Web UI local futura
          ↓
ApplicationService v2
          ↓
Domain Services
          ↓
DevPilot Core
```

Los servicios por dominio no reemplazan los motores internos. Los envuelven con una frontera estable y serializable para que la futura API local no importe directamente validadores, MIASI, RepoAnalyzer, CodeReviewEngine, RefactorPlanner, ModelAdapterRouter, LocalStore o AgentOps.

## 4. Archivos creados

```text
src/devpilot_core/application/workspace_service.py
src/devpilot_core/application/validation_service.py
src/devpilot_core/application/miasi_service.py
src/devpilot_core/application/evals_service.py
src/devpilot_core/application/repo_service.py
src/devpilot_core/application/review_service.py
src/devpilot_core/application/refactor_service.py
src/devpilot_core/application/model_service.py
src/devpilot_core/application/observability_service.py
src/devpilot_core/application/history_service.py
tests/test_application_services_v2.py
docs/audits/func_sprint_65_application_service_v2_audit.md
docs/functional_sprint_65_manifest.json
```

## 5. Archivos modificados

```text
README.md
docs/05_operations/runbook.md
docs/devpilot_backlog_fase_F_producto_visual.md
docs/functional_backlog_after_precode.md
docs/02_architecture/c4_container.md
docs/07_interfaces/internal_application_contract.md
src/devpilot_core/application/__init__.py
src/devpilot_core/application/services.py
src/devpilot_core/application/dtos.py
src/devpilot_core/cli.py
tests/test_application_services.py
tests/test_sprint_32_documentation.py ... tests/test_sprint_64_documentation.py
```

## 6. Criterios PASS

- `ApplicationService.application_contract()` reporta `schema_version=2.0`.
- Existen servicios de aplicación por dominio.
- Las respuestas preservan `CommandResult` y `ApplicationResponse`.
- Operaciones no expuestas devuelven `BLOCK` controlado.
- No se implementa API HTTP ni Web UI todavía.
- No se agregan dependencias externas.
- `validate all` no produce findings bloqueantes.

## 7. Criterios BLOCK

- La futura UI debe importar módulos internos del core para operar.
- Se habilita API HTTP antes del contrato OpenAPI de Sprint 66.
- Se expone operación write/execute sin Approval Workflow.
- Se imprime o persiste contenido sensible en responses, reports, traces o metrics.
- Se reabre Desktop como alcance Fase F sin ADR posterior.

## 8. Riesgos y limitaciones

| Riesgo | Mitigación |
|---|---|
| Fachada demasiado amplia | Separación por dominios y tests de contrato. |
| Operaciones con side effects en UI futura | Mantener dry-run/plan-only y exigir PolicyEngine/Approval en sprints posteriores. |
| Contratos API divergentes | Sprint 66 debe mapear `/api/v1` contra `ApplicationService.application_contract()`. |
| Seguridad API incompleta | Sprint 68 debe implementar token/CORS/policy binding. |

## 9. Comandos de verificación

```powershell
python -m devpilot_core app contract --json --write-report
python -m pytest tests/test_application_services_v2.py -q
python -m pytest tests/test_application_services.py -q
python -m pytest tests/test_sprint_65_documentation.py -q
python -m devpilot_core validate-artifact docs/audits/func_sprint_65_application_service_v2_audit.md --json
python -m devpilot_core schema validate-manifest docs/functional_sprint_65_manifest.json --json
python -m devpilot_core validate all --json
```

## 10. Conclusión

Sprint 65 cierra el nivel `FF-L1 — ApplicationService v2`. DevPilot queda listo para `FUNC-SPRINT-66 — Contratos API y OpenAPI preliminar`, sin haber adelantado servidor, frontend ni dependencias de interfaz.
