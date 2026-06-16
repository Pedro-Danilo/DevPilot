---
title: "DevPilot Local — Backlog ejecutable Fase F: Producto visual"
doc_id: "DEVPL-FUNC-BACKLOG-FASE-F-001"
status: "approved"
version: "1.8.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
updated: "2026-06-16"
source_repo: "repo_DevPilot_Local_89.zip"
source_report: "Informe de avance DevPilot - sprint 0 - 18.docx"
source_backlog_model: "docs/functional_backlog_after_precode.md"
baseline_dependency: "Fases A-E cerradas; Fase E validada por FUNC-SPRINT-63"
first_sprint: "FUNC-SPRINT-64"
last_planned_sprint: "FUNC-SPRINT-73"
change_policy: "controlled_changes_allowed_via_docs_as_code"
approval_scope: "phase_f_executable_backlog_review"
approved_on: "2026-06-14"
approval: "approved_after_phase_e_agentops_closure"
first_open_sprint: "FUNC-SPRINT-72"
last_completed_sprint: "FUNC-SPRINT-71"
next_sprint: "FUNC-SPRINT-72"
phase_f_status: "implementation_in_progress_sprint_71_completed"
ui_strategy: "web_local_first_web_real_ready_desktop_deferred"
---

# DevPilot Local — Backlog ejecutable Fase F: Producto visual

## Estado de aprobación funcional

Este documento queda promovido a estado `approved` después del cierre validado de `FUNC-SPRINT-63 — AgentOps Quality Gate y cierre Fase E`. Su propósito es convertir la **Fase F — Producto visual** en un backlog de implementación ejecutable, siguiendo el modelo operativo usado en `docs/functional_backlog_after_precode.md`.

La Fase F corresponde a la **Ola 9 — API local y Web UI local web-ready**. Parte del estado real de `repo_DevPilot_Local_80.zip`, donde DevPilot ya dispone de `ApplicationService`, DTOs, `app contract`, CLI funcional, core modular y AgentOps local. La fase no debe reescribir el core ni duplicar validadores en la UI. Debe exponer el core mediante contratos estables, API local segura y pantallas inicialmente read-only/dry-run.

Decisión de estrategia visual: DevPilot adoptará **Web UI local como interfaz visual canónica de Fase F**, diseñada desde el inicio para evolucionar hacia una **Web UI real** cuando exista madurez de API, seguridad, contratos y operación. La idea de **UI Desktop queda abandonada para Fase F como objetivo de implementación**, y solo podrá reconsiderarse en una fase posterior mediante ADR específica, si existe evidencia de conveniencia de producto, distribución y seguridad.


## Estado aprobado para implementación

La revisión de cierre de `FUNC-SPRINT-63` confirma que este backlog es una continuación apropiada de DevPilot porque Fase E dejó una capa AgentOps local capaz de exponer trazas, métricas, reportes, exporter OTel dry-run y un `agentops status` consumible por API/UI futura. Por tanto, Fase F puede iniciar por `FUNC-SPRINT-64` sin implementar todavía servidor ni frontend, manteniendo la secuencia segura: decisión arquitectónica y threat model antes de API local, y API local antes de UI.

Ajuste de aprobación aplicado: se actualiza la fuente de verdad de `repo_DevPilot_Local_22.zip` a `repo_DevPilot_Local_80.zip`, las entradas de cada sprint quedan condicionadas a Fases A-E cerradas, no solo A-D, y la estrategia visual queda alineada con `ADR-0013 — Web UI first`: local primero, web real después, desktop diferido.



## Estado de implementación Sprint 64

`FUNC-SPRINT-64 — ADR UI/API local y threat model de interfaz` queda implementado en estado `implemented-initial` y con veredicto `PASS`.

Entregables de cierre:

- `docs/02_architecture/adrs/ADR-0013-web-ui-first.md` operacionaliza la estrategia Web UI first.
- `docs/03_security/ui_api_threat_model.md` formaliza amenazas y controles para API local/Web UI local.
- `docs/audits/func_sprint_64_ui_api_adr_audit.md` registra auditoría de cierre.
- `docs/functional_sprint_64_manifest.json` deja trazabilidad funcional.
- `tests/test_sprint_64_documentation.py` asegura sincronización documental.

Alcance real: no se implementa servidor, frontend ni Desktop. La fase queda lista para `FUNC-SPRINT-65 — ApplicationService v2 por dominios`.

## Estado de implementación Sprint 65

`FUNC-SPRINT-65 — ApplicationService v2 por dominios` queda implementado en estado `implemented-initial` y con veredicto `PASS`.

Entregables de cierre:

- `src/devpilot_core/application/services.py` queda actualizado como fachada compuesta por dominios.
- Se crean servicios por dominio para workspace, validation, MIASI, evals, repo, review, refactor, model, history y observability.
- `ApplicationService.application_contract()` pasa a `schema_version=2.0` y lista capacidades/rutas contract-only para la futura API local.
- `ApplicationService.handle(ApplicationRequest)` permite despachar operaciones aprobadas y devuelve `ApplicationResponse`, sin implementar servidor HTTP.
- `tests/test_application_services_v2.py` valida dominios, ApplicationResponse, bloqueo de operaciones no expuestas y delegación mínima.
- `docs/audits/func_sprint_65_application_service_v2_audit.md` y `docs/functional_sprint_65_manifest.json` dejan trazabilidad.

Alcance real: no se implementa API HTTP, OpenAPI, Web UI ni Desktop. La fase queda lista para `FUNC-SPRINT-66 — Contratos API y OpenAPI preliminar`.


## Estado de implementación Sprint 66

`FUNC-SPRINT-66 — Contratos API y OpenAPI preliminar` queda implementado en estado `implemented-initial` y con veredicto `PASS`.

Entregables de cierre:

- `docs/07_interfaces/api_contract_v1.md` define endpoints, requests, responses y errores antes del servidor real.
- `docs/07_interfaces/openapi_v1.json` registra OpenAPI 3.1 estático y versionado para `/api/v1`.
- `docs/07_interfaces/api_service_mapping.md` traza cada endpoint hacia `ApplicationService v2` y su servicio de dominio.
- `tests/test_api_contract.py` valida que OpenAPI y ApplicationService no diverjan.
- `docs/audits/func_sprint_66_api_contract_audit.md` y `docs/functional_sprint_66_manifest.json` dejan trazabilidad.

Alcance real: no se implementa servidor HTTP, FastAPI, token local, CORS, Web UI ni Desktop. La fase queda lista para `FUNC-SPRINT-67 — API local MVP read-only/dry-run`.


## 1. Propósito

La Fase F busca convertir DevPilot de una herramienta principalmente CLI a un producto visual local, manteniendo la CLI como interfaz técnica y evitando que la UI se salte `ApplicationService`, `PolicyEngine`, MIASI, ReportEngine, EventLogger o LocalStore.

En lenguaje operativo, esta fase avanza desde:

```text
CLI + ApplicationService + app contract
```

hacia:

```text
API local segura + Web UI local web-ready + dashboard + viewers + ruta de evolución a Web UI real
```

## 2. Regla central de Fase F

La UI no debe contener lógica de negocio ni ejecutar acciones críticas directamente. Toda operación debe seguir:

```text
UI → API local / adapter → ApplicationService → Core → PolicyEngine/MIASI/Reports/Store
```

Reglas obligatorias:

1. La API local debe escuchar por defecto solo en `127.0.0.1`.
2. La UI inicial debe ser read-only/dry-run para operaciones sensibles.
3. Ninguna pantalla debe invocar módulos internos saltando `ApplicationService`.
4. Toda respuesta API debe derivarse de `CommandResult`/`ApplicationResponse`.
5. Toda operación write/execute debe exigir Approval Workflow de Fase B.
6. La API no debe habilitar CORS amplio por defecto.
7. La API debe tener token local o mecanismo equivalente antes de exponer operaciones sensibles.
8. Desktop queda fuera del alcance de implementación de Fase F; solo podrá reabrirse por ADR posterior, sin auto-update, red externa ni permisos nativos implícitos.

## 3. Alcance de Fase F

Incluye:

- ADR UI/API local;
- ampliación de `ApplicationService` por dominios;
- contratos OpenAPI/JSON Schema;
- API local read-only/dry-run;
- seguridad localhost y token local;
- Web UI local MVP diseñada con separación API-first;
- preparación explícita para evolución futura a Web UI real;
- dashboard de workspace/readiness/MIASI;
- report viewer;
- trace viewer;
- approval center inicial;
- settings UI inicial;
- decisión documentada de diferir Desktop fuera de Fase F;
- cierre de producto visual MVP web-first.

No incluye:

- SaaS inmediato;
- colaboración multiusuario real;
- RBAC industrial completo;
- ejecución remota;
- auto-update;
- exposición pública de la API;
- marketplace;
- multiagente visual avanzado;
- cloud control plane;
- UI Desktop o shell nativo en Fase F.

## 4. Niveles de implementación de Fase F

| Nivel | Nombre | Objetivo | Estado esperado al cierre |
|---|---|---|---|
| FF-L0 | Decisión UI/API | Elegir técnica y límites | ADR aprobable |
| FF-L1 | ApplicationService v2 | Exponer casos de uso por dominio | Services UI-ready |
| FF-L2 | API local | Endpoints read-only/dry-run | FastAPI local o adapter elegido |
| FF-L3 | Seguridad local | Token, localhost, CORS restringido | API protegida |
| FF-L4 | Web UI local MVP | Dashboard y viewers | UI local funcional, API-first |
| FF-L5 | Acciones controladas | Approval center y dry-run actions | UI no destructiva |
| FF-L6 | Cierre web-first | Cierre Fase F y decisión de evolución | Web UI local consolidada; Web real planificada; Desktop diferido |

## 5. Definition of Done transversal

Un sprint de Fase F solo puede cerrarse si cumple:

- no duplica lógica del core en la UI;
- toda operación pasa por `ApplicationService` o adapter formal;
- toda respuesta conserva trazabilidad a `CommandResult`;
- no se exponen secretos en API/UI;
- no hay red externa por defecto;
- API escucha solo en localhost;
- README y runbook se actualizan;
- se agregan pruebas unitarias, contract tests o UI smoke tests;
- `pytest -q` pasa para el core;
- si se agregan dependencias, se documentan y justifican en ADR.

## 6. Convenciones de IDs

| Tipo | Prefijo | Ejemplo |
|---|---|---|
| Sprint funcional | `FUNC-SPRINT-XX` | `FUNC-SPRINT-64` |
| Historia | `US-FUNC-XX-YYY` | `US-FUNC-64-001` |
| Tarea | `FUNC-XX-YYY` | `FUNC-64-003` |
| Prueba | `TEST-FUNC-XX-YYY` | `TEST-FUNC-64-002` |
| Gate | `GATE-FUNC-XX` | `GATE-FUNC-64` |
| Riesgo | `RISK-FUNC-XX-YYY` | `RISK-FUNC-64-001` |
| API | `API-*` | `API-WORKSPACE-STATUS` |
| UI | `UI-*` | `UI-READINESS-DASHBOARD` |

## 7. Roadmap funcional de Fase F

| Ola | Sprints | Resultado esperado |
|---|---|---|
| Ola 9 | FUNC-SPRINT-64 a 73 | API local segura, Web UI local web-ready, viewers, approval/settings iniciales y cierre web-first; Desktop diferido |

## 8. Referencias técnicas externas de apoyo

- FastAPI es una opción natural para API local porque se integra con Python y type hints, y genera contratos/documentación OpenAPI automáticamente.
- La Web UI local debe diseñarse con contratos API estables para permitir evolución futura a Web UI real sin reescribir el core.
- Tauri/Electron/Desktop quedan fuera de Fase F; solo se reconsiderarán mediante ADR posterior si existe justificación de distribución, permisos nativos o experiencia de usuario.
- Cualquier UI debe respetar la separación C4: UI como contenedor, API/adapters como contenedor, core como componente reutilizable.



## FUNC-SPRINT-64 — ADR UI/API local y threat model de interfaz

## Objetivo

Formalizar la estrategia **Web UI first** antes de implementar servidor o frontend: Web UI local como interfaz canónica de Fase F, API local segura como frontera, evolución futura a Web UI real y Desktop diferido fuera de la fase.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-64-001 | Como arquitecto, quiero una ADR para evitar escoger stack visual por impulso. | Existe ADR con comparación y decisión. |
| US-FUNC-64-002 | Como revisor de seguridad, quiero threat model de API local/UI. | Riesgos localhost, token, CORS y acciones sensibles documentados. |
| US-FUNC-64-003 | Como owner, quiero entender por qué Web UI local primero y no Desktop en Fase F. | La ADR explica trade-offs, evolución a Web real y razones para diferir Desktop. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-64-001 | Ratificar/operacionalizar ADR Web UI first | docs/02_architecture/adrs/ADR-0013-web-ui-first.md o ADR complementaria | Decisión web-first explícita. |
| FUNC-64-002 | Crear threat model de interfaz | docs/03_security/ui_api_threat_model.md | Riesgos de API/UI. |
| FUNC-64-003 | Actualizar C4 Container | docs/02_architecture/c4_container.md | Incluye API local y UI futura. |
| FUNC-64-004 | Actualizar internal_application_contract | docs/07_interfaces/internal_application_contract.md | Describe decisión. |
| FUNC-64-005 | Crear manifiesto Sprint 64 | docs/functional_sprint_64_manifest.json | Sincronizado. |

## Archivos previstos

```text
docs/02_architecture/adrs/ADR-0013-web-ui-first.md
docs/03_security/ui_api_threat_model.md
docs/02_architecture/c4_container.md
docs/07_interfaces/internal_application_contract.md
docs/audits/func_sprint_64_ui_api_adr_audit.md
docs/functional_sprint_64_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core validate-artifact docs/03_security/ui_api_threat_model.md --json
python -m devpilot_core app contract --json
python -m pytest -q
```

## Criterios PASS

- ADR ratifica Web UI local como interfaz canónica de Fase F.
- ADR documenta evolución futura a Web UI real y Desktop diferido.
- Threat model cubre localhost, CORS, token, CSRF/local origin, secrets y acciones críticas.
- No se implementa servidor antes de decisión.

## Criterios BLOCK

- No cerrar si reabre Desktop como alcance implementable de Fase F sin ADR posterior.
- No cerrar si no compara Web local, Web real futura y Desktop diferido.
- No cerrar si no define límites read-only/dry-run iniciales.
- No cerrar si no actualiza C4/internal contract.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-64-001 | Elegir stack prematuramente | ADR web-first con alternativas, límites y criterios. |
| RISK-FUNC-64-002 | Subestimar seguridad localhost | Threat model específico. |
| RISK-FUNC-64-003 | UI acoplada al core | Regla obligatoria UI→API/ApplicationService. |
| RISK-FUNC-64-004 | Duplicar esfuerzos con Desktop temprano | Desktop diferido fuera de Fase F; reabrir solo por ADR posterior. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-64-001 | ADR validable | validate-artifact PASS. |
| TEST-FUNC-64-002 | Threat model | Secciones requeridas PASS. |
| TEST-FUNC-64-003 | App contract | Sigue ok=true. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-64: ADR UI/API local y threat model de interfaz. No codifiques servidor ni frontend hasta cerrar decisión documentada.
```
## Estado de implementación Sprint 69

`FUNC-SPRINT-69 — Web UI MVP: dashboard workspace/readiness/MIASI` queda implementado en estado `implemented-initial` y con veredicto `PASS`.

Entregables de cierre:

- `ui/web/`: primera Web UI local read-only/API-only.
- `ui/web/src/api/client.ts`: cliente local para `/api/v1` con token por header.
- `ui/web/src/pages/Dashboard.ts`: dashboard workspace/readiness/standards/MIASI.
- `ui/web/src/components/StatusCard.ts`: tarjetas visuales PASS/WARN/BLOCK/PENDING.
- `ui/web/scripts/smoke-test.mjs`: smoke test sin dependencias externas de ejecución.
- `tests/test_web_ui_mvp.py`: contrato de UI sin imports Python/core ni endpoints destructivos.
- `docs/functional_sprint_69_manifest.json`: manifiesto funcional.
- `docs/audits/func_sprint_69_web_ui_dashboard_audit.md`: auditoría de cierre.

Alcance real: se implementa una Web UI local MVP con Vite/TypeScript orientada a navegador local. La UI consume API local segura y no implementa Report Viewer, Trace Viewer, Approval Center, Settings UI, RBAC/login ni despliegue web real. Es una versión preliminar industrial que habilita la transición hacia `FUNC-SPRINT-70 — Report Viewer y Trace Viewer`.


## Estado de implementación Sprint 68

`FUNC-SPRINT-68 — Seguridad API local: token, CORS restringido y policy binding` queda implementado en estado `implemented-initial` y con veredicto `PASS`.

Entregables de cierre:

- `src/devpilot_core/interfaces/api/security.py` implementa token local temporal, CORS allowlist, rutas públicas mínimas, redacción de token y binding de rutas con `PolicyEngine`.
- `src/devpilot_core/interfaces/api/app.py` aplica middleware de seguridad, headers mínimos y CORS restringido.
- `python -m devpilot_core api token --json` genera un token de sesión local sin persistirlo como reporte.
- `tests/test_api_security.py` valida token ausente/inválido/válido, CORS sin wildcard, headers, policy binding y bloqueo de host remoto.
- `docs/03_security/ui_api_threat_model.md`, `docs/07_interfaces/api_contract_v1.md`, `docs/07_interfaces/openapi_v1.json` y `docs/07_interfaces/api_service_mapping.md` quedan sincronizados con la API `secured-initial`.
- `docs/audits/func_sprint_68_api_security_audit.md` y `docs/functional_sprint_68_manifest.json` dejan trazabilidad.

Alcance real: no se implementa Web UI, RBAC enterprise, login, sesiones, TLS productivo, API remota ni Desktop. La fase queda lista para `FUNC-SPRINT-69 — Web UI MVP: dashboard workspace/readiness/MIASI`.


## Estado de implementación Sprint 67

`FUNC-SPRINT-67 — API local MVP read-only/dry-run` queda implementado en estado `implemented-initial` y con veredicto `PASS`.

Entregables de cierre:

- `src/devpilot_core/interfaces/api/`: adapter FastAPI local MVP.
- `src/devpilot_core/interfaces/api/app.py`: app factory localhost-first.
- `src/devpilot_core/interfaces/api/routers/status.py`: endpoints GET read-only de estado, MIASI, standards, repo inventory, modelos, observabilidad, history y app contract.
- `src/devpilot_core/interfaces/api/routers/validation.py`: endpoints POST de validación/readiness.
- `src/devpilot_core/interfaces/api/routers/actions.py`: endpoints POST dry-run/plan-only de review/refactor.
- `docs/functional_sprint_67_manifest.json`: manifiesto funcional.
- `docs/audits/func_sprint_67_api_local_mvp_audit.md`: auditoría de cierre.
- `tests/test_api_local.py`: pruebas HTTP locales con `TestClient`.

Alcance real: se implementa servidor FastAPI local MVP, pero no se implementa Web UI, token local, CORS restringido, auth/RBAC ni exposición pública. Es una primera versión que debe evolucionar con `FUNC-SPRINT-68 — Seguridad API local: token, CORS restringido y policy binding`.


## FUNC-SPRINT-65 — ApplicationService v2 por dominios

## Objetivo

Expandir ApplicationService para cubrir workspace, validation, MIASI, evals, repo, review, refactor, model, history y observability sin que la UI llame módulos internos.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-65-001 | Como desarrollador UI, quiero consumir servicios de aplicación estables. | Existen métodos por dominio. |
| US-FUNC-65-002 | Como arquitecto, quiero reducir lógica en CLI. | CLI puede delegar en ApplicationService v2. |
| US-FUNC-65-003 | Como auditor, quiero que las respuestas sigan siendo CommandResult/ApplicationResponse. | Contratos se conservan. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-65-001 | Crear servicios por dominio | application/services_*.py | Workspace/Validation/MIASI/Repo/Review/Model/Observability. |
| FUNC-65-002 | Actualizar DTOs | application/dtos.py | Contratos request/response extendidos. |
| FUNC-65-003 | Refactor ligero del CLI hacia services | cli.py | Sin romper comandos. |
| FUNC-65-004 | Agregar tests de servicios | tests/test_application_services_v2.py | Cubre casos principales. |
| FUNC-65-005 | Actualizar app contract | ApplicationService.application_contract | Lista capacidades nuevas. |

## Archivos previstos

```text
src/devpilot_core/application/services.py
src/devpilot_core/application/dtos.py
src/devpilot_core/application/workspace_service.py
src/devpilot_core/application/review_service.py
src/devpilot_core/application/observability_service.py
tests/test_application_services_v2.py
docs/audits/func_sprint_65_application_service_v2_audit.md
docs/functional_sprint_65_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core app contract --json --write-report
python -m devpilot_core readiness-check --strict --json
python -m pytest tests/test_application_services_v2.py -q
python -m pytest -q
```

## Criterios PASS

- ApplicationService cubre dominios principales.
- CLI sigue funcionando.
- App contract refleja capacidades.

## Criterios BLOCK

- No cerrar si UI futura debe importar validators/policy/review directamente.
- No cerrar si rompe comandos existentes.
- No cerrar si omite policy checks para operaciones sensibles.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-65-001 | Refactor amplio con regresión | Migración incremental y pruebas de CLI existentes. |
| RISK-FUNC-65-002 | Servicios demasiado genéricos | Separar por dominio. |
| RISK-FUNC-65-003 | Duplicación de lógica | Delegar al core, no reimplementar. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-65-001 | Servicios devuelven ApplicationResponse | PASS. |
| TEST-FUNC-65-002 | CLI regression | Comandos críticos PASS. |
| TEST-FUNC-65-003 | App contract | Lista capacidades actualizada. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-65: ApplicationService v2 por dominios. Mueve orquestación reusable fuera de CLI sin romper comandos existentes.
```

## FUNC-SPRINT-66 — Contratos API y OpenAPI preliminar

## Objetivo

Formalizar endpoints, requests, responses y errores antes del servidor real, usando schemas de Fase A y ApplicationService v2.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-66-001 | Como frontend developer, quiero conocer endpoints y respuestas antes de implementar pantallas. | Existe contrato API versionado. |
| US-FUNC-66-002 | Como tester, quiero validar que API y ApplicationService coincidan. | Contract tests pasan. |
| US-FUNC-66-003 | Como arquitecto, quiero versionado de API. | `/api/v1` queda definido. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-66-001 | Crear API contract docs | docs/07_interfaces/api_contract_v1.md | Endpoints y payloads. |
| FUNC-66-002 | Crear OpenAPI preliminar estático | docs/07_interfaces/openapi_v1.yaml o json | Contrato validable. |
| FUNC-66-003 | Mapear endpoints a ApplicationService | docs/07_interfaces/api_service_mapping.md | Trazabilidad endpoint→service. |
| FUNC-66-004 | Crear pruebas de contrato estático | tests/test_api_contract.py | Valida estructura básica. |
| FUNC-66-005 | Actualizar schemas si aplica | docs/schemas/* | Contratos sincronizados. |

## Archivos previstos

```text
docs/07_interfaces/api_contract_v1.md
docs/07_interfaces/openapi_v1.yaml
docs/07_interfaces/api_service_mapping.md
tests/test_api_contract.py
docs/audits/func_sprint_66_api_contract_audit.md
docs/functional_sprint_66_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core validate-artifact docs/07_interfaces/api_contract_v1.md --json
python -m pytest tests/test_api_contract.py -q
python -m pytest -q
```

## Criterios PASS

- Existe contrato API v1 antes de servidor.
- Endpoints están mapeados a servicios.
- Errores usan CommandResult/ApplicationResponse.

## Criterios BLOCK

- No cerrar si endpoints no tienen service mapping.
- No cerrar si define acciones write sin approval.
- No cerrar si contratos contradicen app contract.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-66-001 | Contrato desactualizado rápido | Generar tests contractuales. |
| RISK-FUNC-66-002 | Endpoints demasiado amplios | MVP read-only/dry-run. |
| RISK-FUNC-66-003 | Romper versionado | Prefijo `/api/v1` obligatorio. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-66-001 | Contrato validado | Tests parsean OpenAPI. |
| TEST-FUNC-66-002 | Mapping | Cada endpoint tiene service. |
| TEST-FUNC-66-003 | Docs | validate-artifact PASS. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-66: contrato API v1 y OpenAPI preliminar sin servidor real. Mapea cada endpoint a ApplicationService.
```

## FUNC-SPRINT-67 — API local MVP read-only/dry-run

## Objetivo

Implementar una API local mínima, preferiblemente FastAPI si la ADR lo confirma, limitada a endpoints read-only/dry-run y localhost.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-67-001 | Como usuario visual, quiero consultar estado del workspace desde una API local. | `GET /api/v1/workspace/status` responde. |
| US-FUNC-67-002 | Como frontend developer, quiero readiness/MIASI/reportes por API. | Endpoints básicos devuelven JSON. |
| US-FUNC-67-003 | Como security reviewer, quiero que la API no exponga acciones críticas. | Solo read-only/dry-run MVP. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-67-001 | Crear paquete API local | src/devpilot_core/interfaces/api/ | App factory. |
| FUNC-67-002 | Implementar endpoints base | app/routers | workspace, readiness, standards, MIASI, app contract. |
| FUNC-67-003 | Conectar ApplicationService | API layer | Sin lógica duplicada. |
| FUNC-67-004 | Agregar tests HTTP locales | tests/test_api_local.py | TestClient o equivalente. |
| FUNC-67-005 | Actualizar README/runbook | docs | Comandos de API documentados. |

## Archivos previstos

```text
src/devpilot_core/interfaces/api/__init__.py
src/devpilot_core/interfaces/api/app.py
src/devpilot_core/interfaces/api/routers/status.py
src/devpilot_core/interfaces/api/routers/validation.py
tests/test_api_local.py
docs/audits/func_sprint_67_api_local_mvp_audit.md
docs/functional_sprint_67_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --dry-run --json
python -m pytest tests/test_api_local.py -q
python -m pytest -q
```

## Criterios PASS

- API local responde endpoints MVP.
- Host default es 127.0.0.1.
- No hay endpoints write/execute críticos.

## Criterios BLOCK

- No cerrar si API escucha 0.0.0.0 por defecto.
- No cerrar si endpoints llaman módulos internos saltando services.
- No cerrar si agrega dependencias sin ADR/pyproject actualizado.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-67-001 | Dependencia FastAPI no instalada | Documentar en extras opcionales `[api]`. |
| RISK-FUNC-67-002 | Exposición accidental | Host localhost por defecto y warning si cambia. |
| RISK-FUNC-67-003 | Contrato divergente | Tests contra OpenAPI. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-67-001 | Endpoint app contract | HTTP 200 JSON. |
| TEST-FUNC-67-002 | Readiness endpoint | JSON CommandResult. |
| TEST-FUNC-67-003 | No critical actions | Lista de rutas no incluye apply/refactor execute. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-67: API local MVP read-only/dry-run. Usa el stack decidido en la ADR, default localhost, ApplicationService obligatorio y tests HTTP.
```

## FUNC-SPRINT-68 — Seguridad API local: token, CORS restringido y policy binding

## Objetivo

Agregar controles mínimos para que la API local no quede expuesta sin protección y para que operaciones futuras requieran política/aprobación.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-68-001 | Como usuario, quiero que la API local no sea invocable libremente por cualquier proceso. | Token local requerido salvo endpoints públicos mínimos. |
| US-FUNC-68-002 | Como revisor de seguridad, quiero CORS restringido. | CORS no usa wildcard por defecto. |
| US-FUNC-68-003 | Como arquitecto, quiero que API preserve policy decisions. | Policy binding se aplica a endpoints sensibles. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-68-001 | Implementar token local temporal | api/security.py | Token de sesión local. |
| FUNC-68-002 | Configurar CORS restringido | api/app.py | Origins allowlist. |
| FUNC-68-003 | Agregar security headers locales | api middleware | Headers mínimos. |
| FUNC-68-004 | Integrar PolicyEngine en endpoints sensibles | api dependencies | Bloqueo uniforme. |
| FUNC-68-005 | Actualizar threat model | docs/03_security/ui_api_threat_model.md | Controles documentados. |

## Archivos previstos

```text
src/devpilot_core/interfaces/api/security.py
src/devpilot_core/interfaces/api/app.py
tests/test_api_security.py
docs/03_security/ui_api_threat_model.md
docs/audits/func_sprint_68_api_security_audit.md
docs/functional_sprint_68_manifest.json
```

## Comandos objetivo

```powershell
python -m pytest tests/test_api_security.py -q
python -m devpilot_core api token --json
python -m pytest -q
```

## Criterios PASS

- Token requerido para endpoints no públicos.
- CORS restringido por defecto.
- Endpoints sensibles usan policy checks.

## Criterios BLOCK

- No cerrar si CORS wildcard queda habilitado por defecto.
- No cerrar si tokens se escriben en logs.
- No cerrar si la API acepta remote host sin advertencia/bloqueo.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-68-001 | Token en logs | Redacción y no persistencia cruda. |
| RISK-FUNC-68-002 | CORS mal configurado | Tests específicos. |
| RISK-FUNC-68-003 | Falsa seguridad | Documentar como local MVP, no auth enterprise. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-68-001 | Sin token | Endpoint protegido rechaza. |
| TEST-FUNC-68-002 | Con token | Endpoint responde. |
| TEST-FUNC-68-003 | CORS | Wildcard deshabilitado. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-68: seguridad API local con token temporal, CORS restringido y policy binding. No implementes RBAC completo todavía.
```

## FUNC-SPRINT-69 — Web UI MVP: dashboard workspace/readiness/MIASI

## Objetivo

Construir una Web UI local mínima que consulte la API y muestre estado del workspace, readiness, standards y MIASI sin acciones destructivas.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-69-001 | Como owner, quiero ver el estado del proyecto en un dashboard. | Pantalla inicial muestra workspace/readiness/MIASI. |
| US-FUNC-69-002 | Como usuario no técnico, quiero entender PASS/BLOCK sin leer JSON crudo. | UI traduce findings a tarjetas claras. |
| US-FUNC-69-003 | Como desarrollador, quiero que la UI consuma API, no core directo. | Frontend solo llama endpoints. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-69-001 | Crear estructura frontend | ui/web/ | Proyecto mínimo. |
| FUNC-69-002 | Crear dashboard inicial | ui/web/src | Workspace/Readiness/MIASI cards. |
| FUNC-69-003 | Crear cliente API tipado básico | ui/web/src/api | Consume `/api/v1`. |
| FUNC-69-004 | Agregar UI smoke tests | tests o ui tests | Render básico. |
| FUNC-69-005 | Actualizar docs de ejecución UI | README/runbook | Pasos claros. |

## Archivos previstos

```text
ui/web/package.json
ui/web/src/main.*
ui/web/src/api/client.*
ui/web/src/pages/Dashboard.*
ui/web/src/components/StatusCard.*
docs/audits/func_sprint_69_web_ui_dashboard_audit.md
docs/functional_sprint_69_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core api serve --host 127.0.0.1 --port 8787
cd ui/web && npm test
python -m pytest -q
```

## Criterios PASS

- Dashboard consume API local.
- No hay acciones write/execute.
- Estados PASS/WARN/BLOCK se muestran claramente.

## Criterios BLOCK

- No cerrar si frontend importa código Python/core.
- No cerrar si requiere API externa.
- No cerrar si no documenta instalación frontend.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-69-001 | Stack frontend no decidido | Depende de ADR Sprint 64. |
| RISK-FUNC-69-002 | Complejidad UI temprana | Limitar a dashboard MVP. |
| RISK-FUNC-69-003 | Falta Node en entorno | Documentar prerequisitos y mantener CLI funcional. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-69-001 | Dashboard render | Smoke test PASS. |
| TEST-FUNC-69-002 | API mocked/local | Cliente maneja errores. |
| TEST-FUNC-69-003 | Core regression | pytest PASS. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-69: Web UI MVP con dashboard workspace/readiness/MIASI. Mantén UI read-only, API-only y sin acciones destructivas.
```

## Estado de implementación Sprint 70

`FUNC-SPRINT-70 — Report Viewer y Trace Viewer` queda implementado en estado `implemented-initial` y con veredicto `PASS` focalizado. El viewer consume reportes/trazas/métricas únicamente por API local segura, aplica redacción y límites, y no permite lectura directa del filesystem desde la Web UI. Quedan para evolución futura paginación avanzada, viewer de árbol más rico, búsqueda global y endurecimiento UX.

## FUNC-SPRINT-70 — Report Viewer y Trace Viewer

## Objetivo

Agregar vistas visuales para consultar reportes, findings, traces y métricas de Fase E.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-70-001 | Como auditor, quiero explorar reportes sin abrir archivos manualmente. | Report Viewer lista y abre reportes. |
| US-FUNC-70-002 | Como operador, quiero inspeccionar trazas visualmente. | Trace Viewer muestra árbol de spans. |
| US-FUNC-70-003 | Como usuario, quiero filtrar findings por severidad. | Filtros básicos disponibles. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-70-001 | Crear endpoints de report index si faltan | API | List/read report. |
| FUNC-70-002 | Crear Report Viewer | UI | Lista reportes y detalle. |
| FUNC-70-003 | Crear Trace Viewer | UI | Árbol trace/span. |
| FUNC-70-004 | Crear filtros por severidad/fecha/comando | UI/API | Filtros básicos. |
| FUNC-70-005 | Agregar tests | UI/API | Smoke y contract. |

## Archivos previstos

```text
src/devpilot_core/interfaces/api/routers/reports.py
src/devpilot_core/interfaces/api/routers/traces.py
ui/web/src/pages/Reports.*
ui/web/src/pages/Traces.*
ui/web/src/components/FindingTable.*
tests/test_api_reports_traces.py
docs/audits/func_sprint_70_report_trace_viewer_audit.md
docs/functional_sprint_70_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core trace report --json
python -m devpilot_core metrics summary --json
python -m pytest tests/test_api_reports_traces.py -q
cd ui/web && npm test
python -m pytest -q
```

## Criterios PASS

- Report Viewer no lee filesystem fuera de API.
- Trace Viewer maneja trazas vacías.
- Findings se filtran sin exponer secretos.

## Criterios BLOCK

- No cerrar si UI accede directamente a outputs/.
- No cerrar si reportes revelan secretos.
- No cerrar si trazas grandes bloquean UI sin paginación/límites.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-70-001 | Volumen de reportes | Paginación/límites. |
| RISK-FUNC-70-002 | Datos sensibles | Redacción API y UI. |
| RISK-FUNC-70-003 | UX confusa | Estados y severidades con textos claros. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-70-001 | List reports | Endpoint PASS. |
| TEST-FUNC-70-002 | Trace tree | Render smoke. |
| TEST-FUNC-70-003 | Finding filters | Prueba básica. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-70: Report Viewer y Trace Viewer sobre API local. No permitas lectura directa del filesystem desde la UI.
```

## FUNC-SPRINT-71 — Approval Center y acciones dry-run desde UI

## Objetivo

Exponer aprobación humana y acciones dry-run seguras desde UI, sin habilitar ejecución destructiva desde el frontend.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-71-001 | Como supervisor, quiero revisar solicitudes de aprobación. | Approval Center lista pending/approved/denied. |
| US-FUNC-71-002 | Como usuario, quiero lanzar acciones dry-run seguras desde UI. | UI puede ejecutar readiness, code-review, refactor-plan en dry-run. |
| US-FUNC-71-003 | Como auditor, quiero evidencia de cada decisión. | Cada aprobación tiene trace/report. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-71-001 | Crear endpoints approval | API | request/list/approve/deny si Fase B existe. |
| FUNC-71-002 | Crear Approval Center UI | ui/web | Lista y detalle. |
| FUNC-71-003 | Crear Action Launcher dry-run | ui/web | Readiness/code-review/refactor-plan. |
| FUNC-71-004 | Integrar PolicyEngine | API | Bloqueo de acciones críticas. |
| FUNC-71-005 | Agregar tests | API/UI | Approval y dry-run. |

## Archivos previstos

```text
src/devpilot_core/interfaces/api/routers/approvals.py
src/devpilot_core/interfaces/api/routers/actions.py
ui/web/src/pages/Approvals.*
ui/web/src/components/DryRunActionForm.*
tests/test_api_approvals_actions.py
docs/audits/func_sprint_71_approval_center_audit.md
docs/functional_sprint_71_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core approval list --json
python -m pytest tests/test_api_approvals_actions.py -q
cd ui/web && npm test
python -m pytest -q
```

## Criterios PASS

- UI puede ver y gestionar approvals si Fase B está implementada.
- Acciones desde UI son dry-run o requieren approval válido.
- No hay patch apply/refactor execute libre.

## Criterios BLOCK

- No cerrar si UI permite ejecutar acciones críticas sin approval.
- No cerrar si no se registra auditoría.
- No cerrar si approval_id se expone en logs de forma insegura.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-71-001 | Fase B incompleta | Marcar endpoints como disabled si ApprovalWorkflow no existe. |
| RISK-FUNC-71-002 | Confusión entre dry-run y execute | Etiquetas visuales claras. |
| RISK-FUNC-71-003 | Acciones peligrosas | Policy binding obligatorio. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-71-001 | Approval list | Endpoint PASS o disabled controlado. |
| TEST-FUNC-71-002 | Dry-run action | Readiness desde UI PASS. |
| TEST-FUNC-71-003 | Critical action block | Sin approval bloquea. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-71: Approval Center y acciones dry-run desde UI. Si ApprovalWorkflow aún no existe, expón estado disabled controlado, no mocks engañosos.
```

## FUNC-SPRINT-72 — Settings UI: workspace, providers y políticas locales

## Objetivo

Crear pantallas de configuración inicial para workspace, providers y policy en modo seguro, evitando edición destructiva o secretos en texto claro.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-72-001 | Como usuario, quiero ver configuración del workspace. | Settings muestra project.yaml y estado. |
| US-FUNC-72-002 | Como usuario avanzado, quiero ver providers disponibles. | Providers se listan sin secretos. |
| US-FUNC-72-003 | Como revisor de seguridad, quiero evitar edición insegura de providers/policies. | Cambios write quedan plan-only o approval-gated. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-72-001 | Crear endpoints settings read-only | API | workspace/providers/policy. |
| FUNC-72-002 | Crear Settings UI | ui/web | Páginas de configuración. |
| FUNC-72-003 | Crear providers editor plan-only | UI/API | Genera plan, no escribe secretos. |
| FUNC-72-004 | Agregar redacción de secretos | API/UI | No muestra valores sensibles. |
| FUNC-72-005 | Actualizar runbook | docs | Uso y límites. |

## Archivos previstos

```text
src/devpilot_core/interfaces/api/routers/settings.py
ui/web/src/pages/Settings.*
ui/web/src/components/ProviderSettings.*
tests/test_api_settings.py
docs/audits/func_sprint_72_settings_ui_audit.md
docs/functional_sprint_72_manifest.json
```

## Comandos objetivo

```powershell
python -m devpilot_core model providers --json
python -m pytest tests/test_api_settings.py -q
cd ui/web && npm test
python -m pytest -q
```

## Criterios PASS

- Settings muestra configuración sin secretos.
- Edición de providers es plan-only o approval-gated.
- No se escribe `.devpilot/providers.yaml` sin confirmación controlada.

## Criterios BLOCK

- No cerrar si UI muestra API keys.
- No cerrar si permite editar policy sin approval.
- No cerrar si providers externos se habilitan por accidente.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-72-001 | Secreto en UI | Redacción y tests con secretos sintéticos. |
| RISK-FUNC-72-002 | Configuración inválida | Schema validation previa. |
| RISK-FUNC-72-003 | Activar API externa | CostGuard y disabled por defecto. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-72-001 | Providers read | Sin secretos. |
| TEST-FUNC-72-002 | Plan-only edit | No escribe archivo. |
| TEST-FUNC-72-003 | Settings render | Smoke PASS. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-72: Settings UI para workspace/providers/policy en modo seguro. No guardes secretos ni habilites externos por defecto.
```

## FUNC-SPRINT-73 — Cierre Fase F web-first y decisión de evolución

## Objetivo

Cerrar la Fase F con un producto visual MVP web-first, documentar la ruta de evolución de Web UI local a Web UI real y mantener Desktop diferido fuera del alcance, salvo decisión posterior explícita en una fase futura.

## Entradas

- `repo_DevPilot_Local_81.zip` como baseline vigente.
- Backlogs Fase A–E cerrados; Fase E validada por `FUNC-SPRINT-63`.
- `docs/functional_backlog_after_precode.md` como modelo operativo.
- `Informe de avance DevPilot - sprint 0 - 18.docx` como informe de estado y brechas.

## Historias

| ID | Historia | Criterio de aceptación |
|---|---|---|
| US-FUNC-73-001 | Como usuario, quiero abrir DevPilot como app local o web local. | Existe shell preliminar o decisión postergada justificada. |
| US-FUNC-73-002 | Como owner, quiero reporte de cierre de producto visual. | Cierre Fase F documenta capacidades y brechas. |
| US-FUNC-73-003 | Como arquitecto, quiero que CLI/API/UI estén sincronizados. | Quality gate visual valida endpoints, UI y core. |

## Tareas

| ID | Tarea | Entregable | PASS |
|---|---|---|---|
| FUNC-73-001 | Crear documento de evolución Web real y postergación Desktop | docs/audits/phase_f_visual_product_closure_report.md o ADR update | Web real planificada; Desktop diferido. |
| FUNC-73-002 | Crear Visual Product Quality Gate | tests/scripts | Verifica API/UI/core. |
| FUNC-73-003 | Generar cierre Fase F | docs/audits/phase_f_visual_product_closure_report.md | Estado real. |
| FUNC-73-004 | Actualizar README/runbook | docs | Instrucciones visuales. |
| FUNC-73-005 | Crear release visual MVP manifest | docs/release | Manifest del producto visual. |

## Archivos previstos

```text
scripts/visual_product_smoke.py
docs/audits/phase_f_visual_product_closure_report.md
docs/release/release_manifest_visual_mvp.json
docs/functional_sprint_73_manifest.json
README.md
docs/05_operations/runbook.md
```

## Comandos objetivo

```powershell
python scripts/visual_product_smoke.py --dry-run
python -m devpilot_core app contract --json
python -m devpilot_core agentops status --json
cd ui/web && npm test
python -m pytest -q
```

## Criterios PASS

- Fase F produce Web UI MVP verificable y decisión clara de diferir Desktop fuera de la fase.
- CLI sigue siendo funcional.
- API/UI no habilitan acciones críticas sin approval.

## Criterios BLOCK

- No cerrar si se implementa Desktop shell en Fase F sin ADR posterior explícita.
- No cerrar si UI requiere cloud.
- No cerrar si no hay reporte de cierre.

## Riesgos y mitigaciones

| ID | Riesgo | Mitigación |
|---|---|---|
| RISK-FUNC-73-001 | Empaquetado complejo | Permitir cierre con shell preliminar o postergación justificada. |
| RISK-FUNC-73-002 | Regresión CLI por UI | Smoke core obligatorio. |
| RISK-FUNC-73-003 | Dependencias frontend inestables | Documentar versiones y lockfile. |

## Pruebas mínimas

| ID | Prueba | Evidencia esperada |
|---|---|---|
| TEST-FUNC-73-001 | Visual smoke | API/UI/core check PASS. |
| TEST-FUNC-73-002 | Cierre documental | validate-artifact PASS. |
| TEST-FUNC-73-003 | Regresión total | pytest PASS. |

## Prompt operativo sugerido

```text
Implementa FUNC-SPRINT-73: cierre Fase F con Visual Product Quality Gate, reporte de cierre web-first y plan de evolución a Web UI real. Mantén Desktop diferido salvo ADR posterior.
```

## Cierre esperado de Fase F

Al cerrar Fase F, DevPilot debe disponer de una experiencia Web UI local mínima y web-ready, respaldada por API local segura, ApplicationService v2, report/trace viewers, approval/settings iniciales y documentación de ejecución. La CLI debe seguir siendo una interfaz plenamente soportada. La Web UI real queda como evolución posterior natural; Desktop permanece diferido y sujeto a nueva ADR.


## Estado de implementación Sprint 71

`FUNC-SPRINT-71 — Approval Center y acciones dry-run desde UI` queda implementado como primera versión preliminar industrializable. El alcance habilita endpoints API para approvals, Approval Center UI y Action Launcher dry-run, pero mantiene bloqueada cualquier ejecución destructiva desde frontend. La siguiente iteración abierta es `FUNC-SPRINT-72`.
