---

doc_id: "POST-H-014-BACKLOG"
id: "POST-H-014"
title: "POST-H-014 — UI/API industrial shell"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-23"
approval: "pending_owner_review"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-014 — UI/API industrial shell

## 1. Objetivo

Fortalecer la shell local de producto de DevPilot compuesta por **API local FastAPI** y **Web UI local**, elevándola desde `implemented-initial` hacia una base industrial local, sin convertirla en SaaS, sin habilitar remote execution, sin conectores write y sin plugins ejecutables.

El objetivo es que la UI/API sirvan como superficie operacional segura para consultar madurez, reportes, trazas, aprobaciones, settings y acciones dry-run, manteniendo `ApplicationService` como frontera obligatoria y `PolicyEngine` como guardrail transversal.

## 2. Contexto y justificación

El reverse engineering post-H identificó que ya existen:

```text
src/devpilot_core/interfaces/api/app.py
src/devpilot_core/interfaces/api/dependencies.py
src/devpilot_core/interfaces/api/security.py
src/devpilot_core/interfaces/api/routers/actions.py
src/devpilot_core/interfaces/api/routers/approvals.py
src/devpilot_core/interfaces/api/routers/reports.py
src/devpilot_core/interfaces/api/routers/settings.py
src/devpilot_core/interfaces/api/routers/status.py
src/devpilot_core/interfaces/api/routers/validation.py
ui/web/src/pages/Dashboard.ts
ui/web/src/pages/ApprovalCenterView.ts
ui/web/src/pages/ReportTraceView.ts
ui/web/src/pages/SettingsView.ts
ui/web/src/components/DryRunActionForm.ts
```

La capacidad existe, pero su madurez es inicial. Los riesgos principales son:

```text
- Divergencia CLI/API/UI por saltarse ApplicationService.
- Acciones sensibles expuestas sin contrato de ruta suficiente.
- Inconsistencia entre DTOs internos y payloads HTTP.
- UI que aparenta ejecución real cuando solo debe operar en dry-run.
- Falta de contrato industrial para rutas, errores, estados y permisos.
- Seguridad local insuficiente si el API se expone fuera de localhost.
- Falta de test contract por endpoint y flujo UI crítico.
```

## 3. Alcance

Incluye:

```text
- Route Contract Registry para API local.
- Contrato de exposición UI/API por operación.
- Endpoints normalizados a ApplicationService.
- Respuestas homogéneas ApplicationResponse/CommandResult.
- UI shell con estados claros: PASS/FAIL/BLOCK/ERROR.
- Vistas industriales para status, maturity, reports, traces, approvals y settings.
- API auth local endurecida sin multiusuario enterprise.
- UI smoke tests y API contract tests.
- Quality gate para impedir rutas sensibles sin policy binding.
```

No incluye:

```text
- SaaS.
- Exposición pública en internet.
- Multi-tenant.
- Remote execution.
- Connector write.
- Plugin execution.
- Deploy productivo cloud.
- Autenticación enterprise/OIDC obligatoria.
- Operaciones destructivas desde UI.
```

## 4. Fuentes de entrada obligatorias

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/02_architecture/post_h_current_architecture_map.md
docs/03_security/post_h_security_risk_register.md
docs/05_operations/runbook.md
src/devpilot_core/interfaces/api/
src/devpilot_core/application/
src/devpilot_core/policy/
src/devpilot_core/approval/
src/devpilot_core/identity/
ui/web/src/
tests/test_visual_product_smoke.py
scripts/visual_product_smoke.py
.devpilot/testing/test_contract_registry.json
```

## 5. Entregables

```text
docs/schemas/api_route_contract_registry.schema.json
docs/schemas/ui_route_contract.schema.json
.devpilot/interfaces/api_route_contract_registry.json
.devpilot/interfaces/ui_route_contract_registry.json
src/devpilot_core/interfaces/api/contracts.py
src/devpilot_core/interfaces/api/route_registry.py
src/devpilot_core/interfaces/api/response_mapping.py
src/devpilot_core/application/interface_contracts.py
tests/test_post_h_014_api_route_contracts.py
tests/test_post_h_014_ui_api_boundary.py
tests/test_post_h_014_ui_shell_smoke.py
docs/07_interfaces/ui_api_industrial_shell.md
docs/05_operations/ui_api_local_runbook.md
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/interfaces/api/app.py
src/devpilot_core/interfaces/api/security.py
src/devpilot_core/interfaces/api/routers/*.py
ui/web/src/api/types.ts
ui/web/src/api/client.ts
ui/web/src/pages/*.ts
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

### 6.1 API route contract

```json
{
  "schema_version": "1.0",
  "route_id": "api.status.health",
  "method": "GET",
  "path": "/api/v1/status/health",
  "operation": "status.health",
  "application_service_required": true,
  "policy_check_required": false,
  "auth_required": true,
  "local_only": true,
  "dry_run_only": true,
  "mutations_allowed": false,
  "external_api_allowed": false,
  "remote_execution_allowed": false,
  "response_contract": "ApplicationResponse",
  "risk_level": "low",
  "owner": "interfaces.api"
}
```

### 6.2 UI route contract

```json
{
  "route_id": "ui.dashboard",
  "path": "/",
  "page_component": "Dashboard",
  "allowed_api_routes": ["api.status.health", "api.reports.list"],
  "shows_mutation_controls": false,
  "dry_run_badge_required": true,
  "operator_warning_required": false,
  "owner": "ui.web"
}
```

## 7. Principios de diseño

```text
1. ApplicationService-first: la API no debe saltar al core salvo adapters explícitos aprobados.
2. Policy-aware: toda acción sensible debe tener policy binding.
3. Local-only: la shell es local por defecto.
4. Dry-run visibility: la UI debe mostrar claramente cuándo una acción es simulada.
5. No accidental execution: ningún botón debe ejecutar remote, connector write o plugin execution.
6. Contract-driven API: cada ruta debe tener contrato versionado.
7. Testable UI: flujos críticos deben tener smoke o contract tests.
```

## 8. Micro-sprints propuestos

### POST-H-014-A — Route Contract Registry y API inventory

Objetivo: inventariar rutas API existentes y crear un registry contractual.

Tareas:

```text
1. Crear api_route_contract_registry.schema.json.
2. Crear .devpilot/interfaces/api_route_contract_registry.json.
3. Extraer rutas existentes de routers FastAPI.
4. Clasificar cada ruta por operación, método, path, riesgo, auth y mutations_allowed.
5. Validar que rutas de acciones sensibles tengan policy_check_required=true.
6. Crear tests de schema y consistencia route registry ↔ routers.
```

Criterios PASS:

```text
PASS si toda ruta API aparece en el registry.
PASS si todo contrato tiene method, path, operation, owner, risk_level y response_contract.
PASS si rutas con mutations_allowed=true quedan bloqueadas salvo justificación explícita.
PASS si remote_execution_allowed=false en todas las rutas.
```

Criterios BLOCK:

```text
BLOCK si existe ruta API no registrada.
BLOCK si una ruta sensible no exige auth/policy.
BLOCK si se habilita remote execution o connector write.
```

### POST-H-014-B — Response mapping y errores homogéneos

Objetivo: normalizar respuestas API a `ApplicationResponse` y mapas de error explícitos.

Tareas:

```text
1. Crear response_mapping.py.
2. Definir conversión CommandResult → ApplicationResponse.
3. Definir códigos HTTP para PASS/FAIL/BLOCK/ERROR.
4. Evitar leaks de stack traces en respuestas HTTP.
5. Agregar tests de mapeo.
```

Criterios PASS:

```text
PASS si todas las rutas retornan estructura homogénea.
PASS si BLOCK no se presenta como éxito HTTP ambiguo.
PASS si errores técnicos quedan redactados.
```

### POST-H-014-C — UI Route Contract y shell de producto

Objetivo: contractar navegación UI y acoplarla a rutas API permitidas.

Tareas:

```text
1. Crear ui_route_contract.schema.json.
2. Crear ui_route_contract_registry.json.
3. Alinear Dashboard, Reports, Traces, Approvals y Settings con contratos.
4. Mostrar badges local-first, dry-run, no-remote.
5. Asegurar empty/error/loading states.
6. Crear smoke tests por página.
```

Criterios PASS:

```text
PASS si toda página crítica tiene contrato.
PASS si UI no oculta estados BLOCK/ERROR.
PASS si acciones dry-run muestran claramente su naturaleza.
```

### POST-H-014-D — Security hardening local de API/UI

Objetivo: reforzar controles locales de API y UI sin crear auth enterprise.

Tareas:

```text
1. Revisar API token y headers de seguridad.
2. Confirmar CORS local restrictivo.
3. Agregar endpoint/diagnóstico de security posture local.
4. Bloquear inicio no local salvo flag explícito future/disabled.
5. Validar que settings no muestren secretos.
6. Agregar tests de seguridad API.
```

Criterios PASS:

```text
PASS si API local requiere token en rutas no públicas.
PASS si CORS restringe orígenes por defecto.
PASS si secrets no aparecen en UI ni respuestas API.
```

### POST-H-014-E — Quality gate UI/API industrial shell

Objetivo: integrar la shell al quality gate y documentar operación.

Tareas:

```text
1. Agregar subgate ui-api-industrial-shell.
2. Validar route registry, UI registry y smoke tests.
3. Documentar runbook local.
4. Actualizar test contract registry.
5. Generar reporte outputs/reports/ui_api_shell_report.json.
```

Criterios PASS:

```text
PASS si quality-gate hardening incorpora señal UI/API.
PASS si no hay rutas no contractadas.
PASS si la documentación operacional está aprobada.
```

## 9. Comandos de validación esperados

```powershell
python -m devpilot_core schema validate --schema-id ApiRouteContractRegistry --instance .devpilot/interfaces/api_route_contract_registry.json --json
python -m devpilot_core schema validate --schema-id UiRouteContractRegistry --instance .devpilot/interfaces/ui_route_contract_registry.json --json
python -m pytest tests/test_post_h_014_api_route_contracts.py -q
python -m pytest tests/test_post_h_014_ui_api_boundary.py -q
python -m pytest tests/test_post_h_014_ui_shell_smoke.py -q
python -m devpilot_core quality-gate run --profile hardening --json
```

## 10. No-go gates

```text
NO-GO si una ruta API permite remote_execution_allowed=true.
NO-GO si una ruta sensible no exige auth.
NO-GO si la UI permite acción destructiva sin approval.
NO-GO si secrets aparecen en payloads.
NO-GO si se exponen conectores write o plugins ejecutables.
```

## 11. Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| UI parece productiva pero solo es shell local | Alta | Badges y disclaimers explícitos. |
| Ruta API bypass ApplicationService | Alta | Route registry + tests. |
| Exposición local insegura | Alta | CORS/token/local-only. |
| Secret leakage en settings | Alta | Redaction tests. |
| Crecimiento paralelo CLI/API/UI | Medio-alto | Boundary con ApplicationService y contracts. |

## 12. Definition of Done

```text
[ ] Todas las rutas API están contractadas.
[ ] Todas las páginas UI críticas están contractadas.
[ ] API responde ApplicationResponse homogéneo.
[ ] UI muestra estados PASS/FAIL/BLOCK/ERROR.
[ ] No hay remote, connector write ni plugin execution.
[ ] Quality gate incluye señal UI/API.
[ ] Runbook UI/API aprobado.
```
