---
title: "Contrato interno de Application Services para CLI/API/Web UI"
doc_id: "DEVPL-INTERFACES-001"
status: "approved"
approval: "approved_after_func_sprint_66_implementation"
version: "1.4.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FUNC-SPRINT-65"
updated: "2026-06-15"
change_policy: "controlled_changes_allowed_via_docs_as_code"
---
# Contrato interno de Application Services para CLI/API/Web UI

## 1. Propósito

Este artefacto define el contrato interno que permitirá que el CLI, la futura API local segura y la Web UI local/web real consuman el mismo **DevPilot Core** sin duplicar reglas de negocio, validadores, gates, políticas ni trazabilidad. Desktop queda diferido fuera de Fase F y solo podrá consumir este contrato si una ADR posterior lo justifica.

`FUNC-SPRINT-18` no implementa una UI completa, no inicia un servidor web, no abre una ventana de escritorio y no agrega dependencias externas. Su alcance es preparar una frontera de servicios testeable y serializable.

## 2. Contexto técnico

DevPilot nació como CLI local-first para madurar primero el core, las políticas, los validadores, los reportes, la observabilidad y los agentes. La evolución visual debe respetar esa decisión: la Web UI local y una futura Web UI real deben ser clientes sobre API local/ApplicationService, no implementaciones paralelas. Desktop queda como shell opcional posterior, no como ruta de Fase F.

La decisión es compatible con una futura arquitectura tipo:

```text
CLI / API local / Web UI local / Web UI real futura
          ↓
ApplicationService + DTOs
          ↓
DevPilot Core: validators, policies, reports, traces, state, MIASI, agents
```

## 3. Componentes implementados

```text
src/devpilot_core/application/dtos.py
src/devpilot_core/application/services.py
src/devpilot_core/application/__init__.py
```

## 4. DTOs serializables

### ApplicationRequest

Representa una solicitud futura desde CLI, API local o Web UI.

Campos principales:

```text
operation
payload
client
dry_run
```

Criterios PASS:

```text
JSON serializable.
No contiene secretos reales.
No contiene estado de transporte.
Mantiene dry_run=true por defecto.
```

Criterios BLOCK:

```text
Transportar API keys o secretos crudos.
Acoplarse de forma irreversible a HTTP, Tauri, Electron o cualquier framework concreto.
Permitir ejecución con side effects por defecto.
```

### ApplicationResponse

Envuelve `CommandResult` en un contrato consumible por interfaces.

Campos principales:

```text
contract
schema_version
operation
ok
exit_code
message
data
findings
generated_at
```

Criterios PASS:

```text
Conserva exit_code y findings.
Es JSON serializable.
No reemplaza CommandResult.
No emite contenidos secretos crudos.
```

Criterios BLOCK:

```text
Perder severidad de findings.
Cambiar la semántica de exit codes.
Ocultar bloqueos de PolicyEngine, SecretGuard o CostGuard.
```

### ServiceCapability

Describe una operación consumible por UI futura.

Incluye:

```text
operation
description
side_effect
dry_run_default
command_equivalent
output_contract
```

### InterfaceRouteContract

Define rutas lógicas, no rutas HTTP activas.

Ejemplo:

```text
POST /application/validators/frontmatter -> validators.validate_frontmatter
```

## 5. ApplicationService

`ApplicationService` expone una fachada para validadores y contratos internos.

Operaciones iniciales:

```text
validate_frontmatter(path, strict=False)
validate_artifact(path, strict=False)
checklist_pre_code(strict=True)
readiness(strict=False)
standards_status()
application_contract()
as_application_response(result, operation=None)
```

## 6. Integración con CLI

A partir de `FUNC-SPRINT-18`, los comandos principales de validación documental pasan por `ApplicationService`:

```text
validate-frontmatter
validate-artifact
checklist-pre-code
readiness-check
standards status
```

El nuevo comando de inspección de contrato es:

```powershell
python -m devpilot_core app contract --json
python -m devpilot_core app contract --json --write-report
```

## 7. Relación con Web UI first y Desktop diferido

Este sprint prepara el core para la estrategia visual web-first:

```text
CLI -> ApplicationService -> Core
Web UI local -> API local segura -> ApplicationService -> Core
Web UI real futura -> API/servicios endurecidos -> ApplicationService -> Core
Desktop opcional posterior -> solo si ADR futura lo justifica -> API/ApplicationService -> Core
```

La tecnología definitiva de API/UI se formaliza en Fase F mediante ADR y threat model. Desktop no se implementa en Fase F y no debe convertirse en una segunda UI independiente.

## 8. Criterios PASS

```text
ApplicationService existe.
DTOs son serializables.
CLI usa ApplicationService para validadores principales.
app contract devuelve JSON parseable.
No hay UI implementada todavía.
No hay servidor ni proceso externo.
No hay dependencias nuevas.
pytest -q pasa completo.
README y runbook quedan sincronizados.
```

## 9. Criterios BLOCK

```text
Agregar framework UI sin ADR.
Duplicar lógica de validadores en una capa visual.
Agregar FastAPI/Tauri/Electron como dependencia en Sprint 18.
Habilitar APIs externas o costos.
Guardar secretos o credenciales en DTOs.
Cambiar el contrato CommandResult sin migración.
```

## 10. Riesgos y evolución

Esta es una primera versión de frontera de aplicación. Todavía no cubre autenticación local, sesiones, autorización por rol, streaming de eventos, WebSocket, servidor local, CSRF/CORS, control de procesos, versionado de API ni compatibilidad hacia atrás formal. IPC/empaquetado desktop quedan diferidos fuera de Fase F.

Evolución recomendada:

```text
FUNC-SPRINT-64: formalizar ADR Web UI first y threat model de API/UI local.
Agregar capa API local solo cuando los contratos estén estables.
Agregar tests de compatibilidad de contratos.
Agregar schemas JSON versionados.
Agregar simulador de cliente Web UI local antes de implementar UI real.
Reabrir Desktop solo por ADR posterior, no dentro de Fase F.
```


## 9. Actualización FUNC-SPRINT-64 — Contrato UI/API Web first

### 9.1 Propósito

Sincronizar el contrato interno con `ADR-0013 — Estrategia UI/API Web first`.

### 9.2 Regla de integración

La futura API local y la Web UI local deben consumir DevPilot mediante `ApplicationService`. La UI no debe importar módulos Python del core, leer filesystem directamente ni ejecutar comandos sensibles por fuera de `PolicyEngine` y `Approval Workflow`.

```text
Web UI local → API local /api/v1 → ApplicationService → DevPilot Core
```

### 9.3 Contrato runtime esperado

`python -m devpilot_core app contract --json` debe reportar:

```text
visual_strategy=web_ui_first
api_local_planned=true
web_ui_local_planned=true
web_ui_real_future=true
desktop_deferred=true
desktop_ready_for_shell=false
web_ready_for_shell=true
```

### 9.4 Criterios PASS/BLOCK

PASS: respuestas derivadas de `CommandResult`/`ApplicationResponse`, rutas lógicas versionables y side effects explícitos. BLOCK: UI/API que duplique validadores, salte ApplicationService o exponga acciones write/execute sin approval.


## 9. Sprint 65 — ApplicationService v2 por dominios

`FUNC-SPRINT-65` amplía el contrato interno desde una fachada inicial de validadores hacia una fachada por dominios. Esta versión sigue siendo `implemented-initial`: define frontera reusable para API/Web, pero no implementa servidor HTTP ni frontend.

Dominios expuestos:

| Dominio | Servicio | Rol | Side effects permitidos |
|---|---|---|---|
| workspace | `WorkspaceApplicationService` | Estado y plan dry-run de workspace | read/dry-run |
| validation | `ValidationApplicationService` | Frontmatter, artifact, checklist, readiness, gateway | none/report explícito por adapter |
| miasi | `MiasiApplicationService` | Validación de Agent/Tool/Policy registries | none |
| evals | `EvaluationApplicationService` | Evals offline | workdir local controlado |
| repo | `RepoApplicationService` | Inventory, analyze, git read-only, quality gates | read-only |
| review | `ReviewApplicationService` | Code/Patch review dry-run | none |
| refactor | `RefactorApplicationService` | Plan-only refactor | none |
| model | `ModelApplicationService` | Providers, health, capabilities, budget, mock/local calls gobernadas | mock/local governed |
| history | `HistoryApplicationService` | LocalStore history | read-only |
| observability | `ObservabilityApplicationService` | Trace report, metrics, AgentOps, OTel dry-run | read/dry-run |

Contrato de integración futuro:

```text
Web UI local → API local /api/v1 → ApplicationService.handle(ApplicationRequest) → DomainService → DevPilot Core
```

Criterios PASS:

```text
ApplicationService.application_contract() lista dominios, capacidades y rutas contract-only.
ApplicationService.handle() devuelve ApplicationResponse.
Operaciones desconocidas devuelven BLOCK controlado.
No hay API HTTP ni frontend implementados por Sprint 65.
```

Criterios BLOCK:

```text
La futura API importa motores internos directamente.
La Web UI importa Python/core directamente.
Una operación write/execute se expone sin PolicyEngine y Approval Workflow.
Se habilita red externa o API paga como requisito de la fachada.
```


## 10. Sprint 66 — Contrato API v1 y OpenAPI preliminar

`FUNC-SPRINT-66` convierte las rutas contract-only de `ApplicationService v2` en un contrato API preliminar versionado. Esta versión sigue sin implementar servidor HTTP: define documentación, OpenAPI estático y matriz de mapping.

Artefactos vinculantes:

- `docs/07_interfaces/api_contract_v1.md`;
- `docs/07_interfaces/openapi_v1.json`;
- `docs/07_interfaces/api_service_mapping.md`;
- `tests/test_api_contract.py`.

Flujo obligatorio futuro:

```text
HTTP /api/v1/* → ApplicationRequest → ApplicationService.handle() → DomainService → CommandResult → ApplicationResponse
```

Reglas de contrato:

- todos los endpoints usan `/api/v1`;
- cada endpoint declara `x-devpilot-operation`;
- cada endpoint tiene mapping a un servicio de dominio;
- todas las respuestas usan `ApplicationResponse`;
- los errores `400/403/422/500` también usan `ApplicationResponse`;
- token/CORS/policy binding no están implementados todavía y quedan para Sprint 68.

Criterios PASS: OpenAPI y app contract coinciden; no hay rutas destructivas; no existe servidor HTTP real. Criterios BLOCK: API futura que importe core directamente, respuesta fuera del envelope, endpoint sin mapping o exposición pública antes de controles de seguridad.

## Sprint 67 — API local MVP read-only/dry-run

`FUNC-SPRINT-67` implementa el primer adapter HTTP local sobre `ApplicationService v2`.

Flujo obligatorio:

```text
HTTP /api/v1/*
  → FastAPI router
    → ApiApplicationRequest / query params
      → ApplicationRequest
        → ApplicationService.handle()
          → DomainService
            → CommandResult
              → ApplicationResponse
```

Reglas vinculantes:

1. Los routers viven en `src/devpilot_core/interfaces/api`.
2. Los routers no pueden importar motores internos del core directamente.
3. Toda operación funcional debe pasar por `ApplicationService`.
4. La API local escucha por defecto en `127.0.0.1:8787`.
5. Sprint 67 no implementa token local ni CORS; esos controles son obligatorios en Sprint 68.
6. No se exponen rutas `apply`, `execute`, `rollback/execute` ni `refactor/execute`.
7. Las operaciones `review.code` y `refactor.plan` siguen siendo dry-run/plan-only.

Estado: `implemented-initial`. La API es suficiente para pruebas HTTP locales y para preparar la Web UI, pero no debe tratarse como superficie segura para exposición pública hasta completar Sprint 68.
