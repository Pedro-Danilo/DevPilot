---
doc_id: "POST-H-007-BACKLOG"
id: "POST-H-007"
title: "POST-H-007 — ApplicationService boundary hardening"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_runtime_features_added_by_backlog: false
no_remote_execution_enabled: true
implementation_status: "closed"
approval: "internal"
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


## 13. Avance de implementación — POST-H-007-A

Estado: `implemented-initial`.

`POST-H-007-A — Inventario de operaciones y bypasses` materializa un análisis estático read-only de la frontera `ApplicationService` sin modificar comportamiento runtime. Este micro-sprint produce un reporte machine-readable y Markdown con operaciones expuestas, métodos de la fachada, servicios de dominio, rutas API, consumo UI/API y comandos CLI que aún no tienen mapping explícito hacia `ApplicationService`.

Artefactos implementados:

```text
src/devpilot_core/application/boundary.py
src/devpilot_core/application/report.py
docs/schemas/application_service_boundary_report.schema.json
docs/07_interfaces/application_service_boundary.md
docs/02_architecture/application_service_boundary_map.md
docs/audits/post_h_007_a_application_service_boundary_inventory_report.md
docs/post_h_007_a_manifest.json
tests/test_post_h_007_application_service_boundary.py
tests/test_application_service_boundary_report_schema.py
```

Criterios PASS cubiertos:

```text
PASS: el reporte enumera operaciones por dominio.
PASS: direct_core_bypass_total se calcula y se documenta.
PASS: no se modifica comportamiento runtime.
PASS: no se habilita remote execution, connector write ni plugin execution.
```

Limitación explícita: `POST-H-007-A` es inventario/advisory. No corrige todos los bypasses; esa normalización se mantiene incremental para `POST-H-007-B/C/D/E`.


## 14. Avance de implementación — POST-H-007-B

Estado: `implemented-initial`.

`POST-H-007-B — Operation catalog y schema` crea el contrato declarativo de operaciones de aplicación requerido por el backlog. El catálogo se deriva del inventario read-only de `POST-H-007-A`, deduplica operaciones, declara mappings CLI/API/UI como arrays explícitos, y agrega metadata obligatoria de riesgo, writes, `policy_required`, `dry_run_default` y cobertura mediante Test Contract Registry.

Artefactos implementados:

```text
src/devpilot_core/application/operation_catalog.py
src/devpilot_core/application/capability_registry.py
docs/schemas/application_operation_catalog.schema.json
docs/audits/post_h_007_b_operation_catalog_report.md
docs/post_h_007_b_manifest.json
tests/test_application_operation_catalog_schema.py
```

Métricas iniciales:

```text
operations_total = 35
domains_total = 18
required_initial_domains_covered_total = 10/10
cli_bound_total = 17
api_bound_total = 27
ui_bound_total = 12
policy_required_total = 7
writes_files_total = 4
operations_without_test_contracts_total = 0
direct_core_bypass_total = 105
```

Criterios PASS cubiertos:

```text
PASS: el catálogo valida contra schema ApplicationOperationCatalog.
PASS: cada operación declara riesgo, writes, policy_required y test coverage.
PASS: CLI/API/UI mappings son opcionales, pero explícitos como arrays.
PASS: no se modifica comportamiento runtime ni se agregan rutas/comandos públicos.
```

Limitación explícita: `POST-H-007-B` es una primera versión contractual. Al cierre de `POST-H-007-B` no normalizaba aún DTOs runtime; esa primera cobertura queda incorporada por `POST-H-007-C`. La boundary policy por cliente queda incorporada por `POST-H-007-D` y la integración inicial CommandDescriptor/ApplicationOperationDescriptor por `POST-H-007-E`.


## 15. Avance de implementación — POST-H-007-C

Estado: `implemented-initial`.

`POST-H-007-C — Normalización DTO de operaciones prioritarias` introduce una ruta runtime incremental para que las operaciones priorizadas por el backlog puedan ejecutarse mediante `ApplicationRequest` y retornar `ApplicationResponse`, preservando el `CommandResult` como resultado core. El cambio endurece el boundary sin alterar rutas públicas, sin agregar comandos CLI y sin habilitar capacidades remotas o write externas.

Operaciones cubiertas:

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

Artefactos implementados:

```text
src/devpilot_core/application/dto_normalization.py
src/devpilot_core/application/services.py
src/devpilot_core/application/__init__.py
tests/test_application_dto_normalization.py
docs/audits/post_h_007_c_dto_normalization_report.md
docs/post_h_007_c_manifest.json
```

Criterios PASS cubiertos:

```text
PASS: las operaciones seleccionadas retornan ApplicationResponse válida.
PASS: findings se preservan durante la conversión desde CommandResult.
PASS: exit_code se conserva durante la conversión.
PASS: data, report_paths y metadata crítica se preservan.
PASS: validation.docs, validation.contracts, settings.status y observability.traces quedan declaradas como operaciones DTO prioritarias.
PASS: no se agregan rutas HTTP públicas, comandos CLI públicos ni enforcement por interfaz.
```

Limitación explícita: `POST-H-007-C` es una primera versión de normalización DTO prioritaria. La autorización por interfaz (`cli`, `api`, `ui`, `automation`, `internal`) queda cubierta de forma inicial por `POST-H-007-D`, y la integración inicial con CLI registry/quality gate queda cubierta por `POST-H-007-E`.


## 16. Avance de implementación — POST-H-007-D

Estado: `implemented-initial`.

`POST-H-007-D — Boundary policy y guardrails por interfaz` introduce una capa `ApplicationBoundaryPolicy` aplicada antes del dispatch de `ApplicationService.execute()`. Esta implementación define clientes formales (`cli`, `api`, `ui`, `automation`, `internal`), reglas permitidas por cliente, enforcement inicial de exposición API/UI, preservación de `dry_run` para operaciones sensibles y uso de `PolicyEngine` antes del handler de dominio cuando la operación lo requiere.

Artefactos implementados:

```text
src/devpilot_core/application/policy.py
src/devpilot_core/application/services.py
src/devpilot_core/application/__init__.py
tests/test_application_boundary_policy.py
docs/audits/post_h_007_d_boundary_policy_report.md
docs/post_h_007_d_manifest.json
```

Métricas iniciales:

```text
rules_total = 39
clients_total = 5
sensitive_operations_total = 7
sensitive_without_policy_required_total = 0
api_allowed_total = 27
ui_allowed_total = 12
automation_allowed_total = 32
publicly_unexposed_operations_total = 12
```

Criterios PASS cubiertos:

```text
PASS: API/UI no pueden ejecutar operaciones no declaradas como expuestas.
PASS: operaciones sensibles requieren policy_required=true o se tratan como sensibles por riesgo/write-like behavior.
PASS: operaciones sensibles ejecutan PolicyEngine antes del handler.
PASS: dry-run se preserva para api/ui/automation en operaciones sensibles.
PASS: no se agregan rutas HTTP públicas, comandos CLI públicos, remote execution, connector write ni plugin execution.
```

Limitación explícita: `POST-H-007-D` es una primera versión de boundary policy dentro del runtime DTO. No corrige todos los bypasses CLI históricos. La integración inicial `CommandDescriptor`/`ApplicationOperationDescriptor` queda incorporada por `POST-H-007-E`, pero la migración completa de comandos legacy sigue siendo incremental.


## 17. Avance de implementación — POST-H-007-E

`POST-H-007-E — Integración con CLI registry y quality gate` conecta el trabajo de `POST-H-006` con la frontera `ApplicationService` de `POST-H-007`. La implementación agrega un reporte local/read-only que relaciona `CommandDescriptor` con `ApplicationOperationDescriptor`, agrega metadata `application_operation_id` a comandos registrados seleccionados y conecta la verificación al perfil `quality-gate hardening`.

Artefactos implementados:

```text
src/devpilot_core/application/cli_integration.py
src/devpilot_core/cli_registry/registry.py
src/devpilot_core/quality/gate.py
tests/test_application_cli_boundary_integration.py
docs/audits/post_h_007_e_cli_boundary_integration_report.md
docs/post_h_007_e_manifest.json
```

Métricas iniciales:

```text
commands_total = 130
registered_commands_total = 23
registered_commands_with_operation_mapping_total = 3
applicable_commands_without_mapping_total = 8
api_ui_operations_total = 27
api_ui_operations_with_contract_total = 27
api_ui_operations_without_contract_total = 0
blocking_findings_total = 0
warnings_total = 8
quality_gate_hardening_bound = true
```

Estado de criterios PASS:

```text
PASS si comandos registrados pueden apuntar a operation_id.
PASS si operaciones API/UI tienen contract explícito.
PASS si test-contracts validate pasa.
PASS si quality-gate hardening conserva estado PASS.
```

Limitación explícita: `POST-H-007-E` no activa runtime registry routing ni migra todos los comandos legacy. Los warnings de mapping son no bloqueantes en esta versión inicial; una versión posterior puede promoverlos a enforcement cuando exista plan de migración o excepciones explícitas por comando.


## 17. Cierre del backlog — POST-H-007

`POST-H-007 — ApplicationService boundary hardening` queda cerrado como `implemented-initial` después de `POST-H-007-E`.

Capacidades adicionadas:

```text
- Inventario ApplicationService/API/UI/CLI y bypasses directos.
- ApplicationOperationCatalog con contratos, riesgos, policy_required, dry_run_default, mappings y test coverage.
- Normalización DTO prioritaria para operaciones ApplicationService.
- Boundary policy por InterfaceClient: cli, api, ui, automation e internal.
- Guardrails API/UI para operaciones no expuestas y operaciones sensibles.
- Integración inicial CLI registry/ApplicationOperationCatalog.
- Subgate application-cli-boundary-integration en quality-gate hardening.
```

Gaps cubiertos:

```text
- Reducción de divergencia CLI/API/UI mediante catálogo declarativo.
- Exposición API/UI explícita y verificable.
- Operaciones sensibles con policy_required y dry-run preservado.
- Test contracts explícitos para operaciones API/UI.
- Warnings no bloqueantes para comandos CLI aún no mapeados a operation_id.
```

Limitaciones que quedan para evolución posterior:

```text
- No se migraron todos los comandos legacy al ApplicationService.
- No se habilitó runtime registry routing.
- Los warnings de comandos aplicables sin operation_id siguen no bloqueantes.
- La promoción de warnings a blockers requiere allowlist/excepciones explícitas en un backlog posterior.
```

El cierre de este backlog habilita `POST-H-008 — Runtime state lifecycle policy`.
