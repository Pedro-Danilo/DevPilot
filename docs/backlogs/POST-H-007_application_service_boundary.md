---
doc_id: "POST-H-007-BACKLOG"
id: "POST-H-007"
title: "POST-H-007 — ApplicationService boundary hardening"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-23"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_runtime_features_added_by_backlog: false
no_remote_execution_enabled: true
---

# POST-H-007 — ApplicationService boundary hardening

## 1. Objetivo

Fortalecer `ApplicationService` como **frontera estable entre CLI/API/UI y el core de DevPilot**, garantizando que las interfaces externas no dependan directamente de motores internos, modelos de bajo nivel o rutas de filesystem sin pasar por servicios de aplicación, contratos DTO, políticas y resultados normalizados.

El objetivo no es crear una nueva capa burocrática, sino reducir divergencias entre CLI, API local y Web UI, estabilizar contratos y preparar DevPilot para madurez `production-ready-local` sin activar capacidades remotas ni riesgosas.

## 2. Contexto y justificación

El reverse engineering post-H confirmó que `ApplicationService` existe y agrupa servicios de workspace, validation, MIASI, evals, repo, reports, approvals, settings, review, refactor, model, history y observability. Sin embargo, varios comandos CLI todavía llaman motores de dominio directamente. Eso es aceptable históricamente, pero genera riesgos:

```text
- CLI, API y UI pueden divergir en semántica.
- PolicyEngine puede aplicarse de forma desigual.
- Contratos ApplicationRequest/ApplicationResponse quedan subutilizados.
- Es difícil auditar qué operaciones están expuestas a cada interfaz.
- La futura UI/API industrial dependerá de un boundary más estricto.
```

Este backlog endurece la frontera sin romper compatibilidad del CLI.

## 3. Alcance

Incluye:

```text
- Inventario de operaciones ApplicationService actuales y faltantes.
- Catálogo machine-readable de capabilities de aplicación.
- Normalización de ApplicationRequest/ApplicationResponse en operaciones prioritarias.
- Boundary policy para CLI/API/UI.
- Tests de paridad entre CLI directo y ApplicationService.
- Reporte de operaciones que aún no pasan por ApplicationService.
```

No incluye:

```text
- Reescritura completa de todos los comandos.
- Cambio de rutas HTTP públicas.
- Cambio visual amplio de UI.
- Nueva autenticación industrial.
- Remote execution.
- Connector write.
- Plugin execution.
```

## 4. Fuentes de entrada obligatorias

```text
src/devpilot_core/application/services.py
src/devpilot_core/application/dtos.py
src/devpilot_core/application/*_service.py
src/devpilot_core/interfaces/api/routers/*.py
src/devpilot_core/cli.py
src/devpilot_core/cli_models.py
docs/07_interfaces/internal_application_contract.md
docs/schemas/application_request.schema.json
docs/schemas/application_response.schema.json
docs/schemas/service_capability.schema.json
docs/schemas/interface_route_contract.schema.json
docs/backlogs/post_h_prioritized_roadmap.md
docs/02_architecture/post_h_current_architecture_map.md
```

## 5. Entregables

```text
src/devpilot_core/application/boundary.py
src/devpilot_core/application/capability_registry.py
src/devpilot_core/application/operation_catalog.py
src/devpilot_core/application/policy.py
src/devpilot_core/application/report.py
docs/schemas/application_operation_catalog.schema.json
docs/07_interfaces/application_service_boundary.md
docs/02_architecture/application_service_boundary_map.md
outputs/reports/application_service_boundary_report.json    # generado, no versionar
outputs/reports/application_service_boundary_report.md      # generado, no versionar
tests/test_post_h_007_application_service_boundary.py
tests/test_application_operation_catalog_schema.py
```

## 6. Modelo de datos mínimo

```json
{
  "schema_version": "1.0",
  "catalog_id": "devpilot-application-operation-catalog",
  "operations": [
    {
      "operation_id": "workspace.status",
      "domain": "workspace",
      "service": "WorkspaceApplicationService",
      "method": "status",
      "request_contract": "ApplicationRequest",
      "response_contract": "ApplicationResponse",
      "cli_commands": ["workspace status"],
      "api_routes": ["GET /api/v1/status"],
      "ui_surfaces": ["Dashboard"],
      "policy_required": false,
      "dry_run_default": true,
      "writes_files": false,
      "risk_level": "low",
      "test_contract_ids": []
    }
  ],
  "summary": {
    "operations_total": 0,
    "cli_bound_total": 0,
    "api_bound_total": 0,
    "ui_bound_total": 0,
    "direct_core_bypass_total": 0
  }
}
```

## 7. Principios de boundary

```text
1. CLI/API/UI no deben inferir reglas de negocio por su cuenta.
2. ApplicationService debe permanecer fino: orquesta, no reimplementa dominio.
3. PolicyEngine se aplica antes de acciones sensibles.
4. Todo retorno público debe normalizarse a CommandResult o ApplicationResponse.
5. Las operaciones read-only deben declararlo explícitamente.
6. Las operaciones con writes deben declarar rutas, dry-run y policy requirements.
7. API/UI no deben leer archivos arbitrarios sin pasar por core/service.
```

## 8. Micro-sprints propuestos

### POST-H-007-A — Inventario de operaciones y bypasses

Objetivo: identificar qué operaciones pasan por `ApplicationService` y cuáles aún invocan core directo.

Tareas:

```text
1. Crear inspector estático de imports/llamadas desde CLI y API.
2. Listar métodos existentes de ApplicationService y servicios de dominio.
3. Identificar comandos CLI que llaman motores directamente.
4. Identificar routers API y componentes UI dependientes de servicios.
5. Generar application_service_boundary_report read-only.
```

Criterios PASS:

```text
PASS si el reporte enumera operaciones por dominio.
PASS si direct_core_bypass_total se calcula y se documenta.
PASS si no se modifica comportamiento runtime.
```

Criterios BLOCK:

```text
BLOCK si el reporte oculta bypasses conocidos.
BLOCK si intenta corregir todos los bypasses sin plan incremental.
```

### POST-H-007-B — Operation catalog y schema

Objetivo: crear contrato declarativo de operaciones de aplicación.

Tareas:

```text
1. Crear ApplicationOperationDescriptor.
2. Crear ApplicationOperationCatalog.
3. Crear schema application_operation_catalog.schema.json.
4. Registrar schema en schema_catalog.json.
5. Mapear operaciones iniciales: workspace, validation, reports, approvals, settings, repo, review, refactor, model, observability.
```

Criterios PASS:

```text
PASS si el catálogo valida contra schema.
PASS si cada operación declara riesgo, writes, policy_required y test coverage.
PASS si CLI/API/UI mappings son opcionales pero explícitos.
```

### POST-H-007-C — Normalización DTO de operaciones prioritarias

Objetivo: asegurar que operaciones prioritarias puedan ejecutarse vía `ApplicationRequest`/`ApplicationResponse`.

Operaciones iniciales recomendadas:

```text
workspace.status
validation.docs
validation.contracts
reports.list
reports.read
approvals.list
settings.status
repo.inventory
review.code
refactor.plan
observability.traces
```

Tareas:

```text
1. Agregar dispatch o adapter interno para operaciones seleccionadas.
2. Mantener CommandResult como core result.
3. Convertir a ApplicationResponse de forma uniforme.
4. Agregar tests de respuesta para CLI/API-equivalent paths.
```

Criterios PASS:

```text
PASS si operaciones seleccionadas retornan ApplicationResponse válida.
PASS si findings se preservan.
PASS si exit_code se conserva.
PASS si no se pierden report_paths ni metadata crítica.
```

### POST-H-007-D — Boundary policy y guardrails por interfaz

Objetivo: declarar reglas de uso de ApplicationService por tipo de interfaz.

Tareas:

```text
1. Definir InterfaceClient: cli, api, ui, automation, internal.
2. Definir operaciones permitidas por cliente.
3. Exigir policy check para operaciones sensibles.
4. Bloquear operaciones no expuestas a API/UI.
5. Documentar reglas en docs/07_interfaces/application_service_boundary.md.
```

Criterios PASS:

```text
PASS si API/UI no pueden ejecutar operaciones no declaradas.
PASS si operaciones sensibles requieren policy_required=true.
PASS si dry-run se preserva por defecto.
```

Criterios BLOCK:

```text
BLOCK si se abre una operación write desde API/UI sin approval/policy.
BLOCK si se reduce seguridad de token/CORS/policy actual.
```

### POST-H-007-E — Integración con CLI registry y quality gate

Objetivo: conectar POST-H-006 y POST-H-007.

Tareas:

```text
1. Relacionar CommandDescriptor con ApplicationOperationDescriptor.
2. Agregar warnings si un comando nuevo no tiene operation mapping cuando aplica.
3. Agregar test contract para boundary.
4. Documentar en runbook cómo agregar operación nueva.
5. Mantener quality-gate hardening en PASS.
```

Criterios PASS:

```text
PASS si comandos registrados pueden apuntar a operation_id.
PASS si operaciones API/UI tienen contract explícito.
PASS si test-contracts validate pasa.
```

## 9. Comandos de validación final

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_post_h_007_application_service_boundary.py -q
python -m pytest tests/test_application_operation_catalog_schema.py tests/test_schema_registry.py -q
python -m devpilot_core schema validate --schema-id ApplicationOperationCatalog --instance outputs/reports/application_operation_catalog.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core industrial-readiness check --json
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Convertir ApplicationService en god object | Alta | Mantenerlo como orquestador fino. |
| Duplicar lógica de dominio | Alta | Servicios llaman core; no reimplementan reglas. |
| Romper CLI por normalización DTO | Alta | Tests de paridad y migración incremental. |
| Exponer operaciones sensibles en API/UI | Crítica | Boundary policy + PolicyEngine + approval. |
| Sobrecargar este hito con UI/API hardening | Media | Limitar a boundary, dejar UI/API industrial shell para POST-H-014. |

## 11. No-go gates

```text
NO-GO si se habilitan writes API/UI sin policy/approval.
NO-GO si se elimina CommandResult como contrato común.
NO-GO si ApplicationService accede a rutas fuera del workspace sin PathGuard.
NO-GO si se activa remote execution.
NO-GO si se habilita connector write o plugin execution.
NO-GO si se rompen comandos CLI existentes.
```

## 12. Entregable verificable

```text
Catálogo de operaciones ApplicationService validable.
Reporte de boundary y bypasses.
Operaciones prioritarias normalizadas vía ApplicationRequest/ApplicationResponse.
Reglas de exposición por interfaz.
Tests focales PASS.
Quality gate hardening PASS.
```
