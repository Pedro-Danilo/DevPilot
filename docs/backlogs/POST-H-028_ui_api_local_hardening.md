---
doc_id: "POST-H-028-BACKLOG"
id: "POST-H-028"
title: "POST-H-028 — UI/API local hardening"
status: "approved"
version: "0.3.0"
owner: "Ordonez"
created: "2026-07-07"
updated: "2026-07-08"
approval: "approved"
phase: "POST-FASE-H"
priority: "P0"
roadmap_wave: "Ola 3"
roadmap_source: "devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md"
onboarding_report_source: "devpilot_onboarding_report_final_compilado.md"
source_repo: "repo_DevPilot_Local_273_POST_H_027-E.zip"
depends_on: "POST-H-026, POST-H-027"
local_first: true
dry_run_default: true
read_only_by_default: true
no_remote_execution_enabled: true
no_external_apis_required: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
claims_allowed: "production-ready-local"
claims_forbidden: "enterprise-ready, remote-ready, SaaS-ready, compliance-certified"
implementation_status: "in-progress/post-h-028-b-implemented-initial"
current_micro_sprint: "POST-H-028-B"
next_micro_sprint: "POST-H-028-C"
---

# POST-H-028 — UI/API local hardening

## 1. Dictamen ejecutivo

POST-H-028 debe elevar la UI/API local desde una shell `implemented-initial` hacia una consola operacional local robusta, sin convertirla en una replica completa de la CLI ni en una superficie de ejecucion privilegiada.

El roadmap v3 define la Ola 3 asi:

```text
Ola 3 - POST-H-028: UI/API local hardening

Objetivo:
Elevar UI/API desde shell local a consola operacional local robusta.

Micro-sprints:
- POST-H-028-A - API contract drift guard
- POST-H-028-B - Local auth and CORS hardening
- POST-H-028-C - Visual smoke tests
- POST-H-028-D - Operator flows and error states
- POST-H-028-E - UI route registry enforcement
```

Este backlog conserva esos cinco micro-sprints. No agrega micro-sprints adicionales porque la Ola 3 ya cubre la secuencia industrial necesaria: primero bloquear drift API, despues endurecer seguridad local, luego probar visualmente, despues madurar flujos de operador y finalmente hacer enforcement del UI route registry.

## 2. Regla de alcance principal

La UI no debe cubrir de forma indiscriminada toda la superficie funcional de la CLI.

Debe cubrir:

```text
- Estado local del producto.
- Evidencia y reportes.
- Trazas y metricas operacionales.
- Operator dashboard.
- Approval Center local.
- Settings redacted/plan-only.
- Acciones dry-run/plan-only permitidas.
- Estados PASS/BLOCK/ERROR/pending.
- No-go gates visibles.
```

Debe permanecer CLI-only o requerir backlog/ADR especifico:

```text
- Diagnostico profundo batch.
- Release y packaging avanzado.
- Migraciones y comandos historicos de mantenimiento.
- Operaciones que escriben fuente.
- rollback execute.
- patch apply.
- refactor execute.
- connector write.
- plugin execution.
- remote execution.
- tests.run arbitrario.
- git push/deploy.
```

La UI debe ser consola operacional local, no atajo privilegiado.

## 3. Fuentes consultadas

Fuentes obligatorias verificadas:

```text
/workspace/.cache/01-devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md
/workspace/.cache/02-repo_DevPilot_Local_262_POST_H_025_E.zip
/workspace/.cache/03-devpilot_onboarding_report_final_compilado.md
```

Repo descomprimido:

```text
/workspace/repo_DevPilot_Local_262_POST_H_025_E
```

Archivos consultados de forma focal:

```text
docs/05_operations/ui_api_local_runbook.md
docs/07_interfaces/api_contract_v1.md
docs/07_interfaces/api_service_mapping.md
docs/07_interfaces/ui_api_industrial_shell.md
docs/07_interfaces/openapi_v1.json
ui/web/README.md
ui/web/package.json
ui/web/src/api/client.ts
ui/web/src/main.ts
ui/web/src/pages/Dashboard.ts
ui/web/src/pages/ReportTraceView.ts
ui/web/src/pages/ApprovalCenterView.ts
ui/web/src/pages/SettingsView.ts
ui/web/src/pages/OperatorDashboard.ts
src/devpilot_core/interfaces/api/app.py
src/devpilot_core/interfaces/api/security.py
src/devpilot_core/interfaces/api/route_registry.py
src/devpilot_core/interfaces/api/shell_gate.py
src/devpilot_core/interfaces/api/ui_contracts.py
.devpilot/interfaces/api_route_contract_registry.json
.devpilot/interfaces/ui_route_contract_registry.json
tests/test_api_contract.py
tests/test_api_local.py
tests/test_api_security.py
tests/test_api_reports_traces.py
tests/test_api_settings.py
tests/test_api_approvals_actions.py
tests/test_post_h_014_api_route_contracts.py
tests/test_post_h_014_security_hardening.py
tests/test_post_h_014_ui_api_shell_gate.py
tests/test_post_h_014_ui_shell_contract.py
tests/test_web_ui_mvp.py
tests/test_web_ui_report_trace_viewer.py
tests/test_web_ui_approval_center.py
tests/test_web_ui_settings.py
tests/test_post_h_015_operator_dashboard_ui.py
```

## 4. Estado base que hereda POST-H-028

El repo 262 contiene una base UI/API real:

```text
- API FastAPI local bajo /api/v1.
- Host local por defecto: 127.0.0.1.
- Token local en X-DevPilot-Token o Authorization Bearer.
- CORS restringido a origenes localhost/loopback.
- Wildcard CORS bloqueado.
- Security posture endpoint protegido.
- API_ROUTE_POLICIES en src/devpilot_core/interfaces/api/security.py.
- ApiRouteContractRegistry con 35 rutas.
- UiRouteContractRegistry con 5 rutas.
- Web UI Vite/TypeScript bajo ui/web.
- DevPilotApiClient consume API local.
- La UI no importa Python/core ni lee filesystem directamente.
- Dashboard, Report/Trace Viewer, Approval Center, Settings y Operator Dashboard.
- Action Launcher limitado a acciones dry-run permitidas.
- Subgate ui-api-industrial-shell.
- npm --prefix ui/web test como smoke contractual.
```

Estado industrial actual:

```text
implemented-initial / secured-initial
```

Brechas que justifican POST-H-028:

```text
- El drift API/OpenAPI/registry puede aparecer si se agregan endpoints.
- La auth local no debe confundirse con auth enterprise.
- El modelo token/CORS/local bind requiere pruebas negativas mas estrictas.
- La UI tiene smoke contractual, pero no pruebas visuales reales robustas.
- La UI debe mostrar estados operacionales completos: loading, empty, error, BLOCK, unauthorized, API down.
- El UI route registry debe pasar de contrato inicial a enforcement bloqueante para paginas nuevas.
- La UI no debe crecer hacia acciones sensibles sin ADR/backlog especifico.
```

## 5. Objetivo del backlog

Implementar hardening UI/API local para que el operador pueda usar la consola local con confianza practica:

```text
1. Toda ruta API expuesta esta contractada y sincronizada.
2. Toda ruta protegida exige token y policy binding.
3. CORS y bind host mantienen local-only.
4. La UI renderiza visualmente los flujos criticos.
5. Los estados de error y BLOCK son visibles y comprensibles.
6. El UI route registry bloquea paginas o flujos no registrados.
7. Las acciones sensibles siguen fuera de UI o permanecen plan-only/dry-run.
```

## 6. No objetivos

POST-H-028 no incluye:

```text
- Login multiusuario.
- OIDC/SSO.
- IAM enterprise.
- Rate limiting industrial.
- Multi-tenant SaaS.
- API publica remota.
- Persistencia de sesiones enterprise.
- Exposicion en red no local.
- Remote execution.
- Connector write.
- Plugin execution.
- patch apply desde UI.
- rollback execute desde UI.
- refactor execute desde UI.
- tests.run arbitrario desde UI.
- Reemplazar la CLI.
```

## 7. Artefactos globales esperados al cierre de POST-H-028

Nuevos artefactos sugeridos:

```text
docs/backlogs/POST-H-028_ui_api_local_hardening.md
docs/POST-H-028_ui_api_local_hardening.md
docs/schemas/api_contract_drift_report.schema.json
docs/schemas/local_api_security_hardening_report.schema.json
docs/schemas/ui_visual_smoke_report.schema.json
docs/schemas/operator_flow_smoke_report.schema.json
docs/schemas/ui_route_enforcement_report.schema.json
.devpilot/interfaces/ui_api_hardening_policy.json
src/devpilot_core/interfaces/api/contract_drift.py
src/devpilot_core/interfaces/api/security_hardening.py
src/devpilot_core/interfaces/api/operator_flow_smoke.py
src/devpilot_core/interfaces/api/ui_route_enforcement.py
ui/web/tests/visual-smoke.spec.ts
ui/web/playwright.config.ts
tests/test_post_h_028_api_contract_drift_guard.py
tests/test_post_h_028_local_auth_cors_hardening.py
tests/test_post_h_028_visual_smoke_contract.py
tests/test_post_h_028_operator_flows_error_states.py
tests/test_post_h_028_ui_route_registry_enforcement.py
docs/audits/post_h_028_a_api_contract_drift_guard_report.md
docs/audits/post_h_028_b_local_auth_cors_hardening_report.md
docs/audits/post_h_028_c_visual_smoke_report.md
docs/audits/post_h_028_d_operator_flows_error_states_report.md
docs/audits/post_h_028_e_ui_route_registry_enforcement_report.md
docs/post_h_028_a_manifest.json
docs/post_h_028_b_manifest.json
docs/post_h_028_c_manifest.json
docs/post_h_028_d_manifest.json
docs/post_h_028_e_manifest.json
```

Runtime outputs esperados, no versionables:

```text
outputs/reports/api_contract_drift_report.json
outputs/reports/local_api_security_hardening_report.json
outputs/reports/ui_visual_smoke_report.json
outputs/reports/operator_flow_smoke_report.json
outputs/reports/ui_route_enforcement_report.json
outputs/ui-smoke/screenshots/
```

Artefactos a mantener sincronizados:

```text
README.md
docs/05_operations/runbook.md
docs/05_operations/ui_api_local_runbook.md
docs/07_interfaces/api_contract_v1.md
docs/07_interfaces/api_service_mapping.md
docs/07_interfaces/ui_api_industrial_shell.md
docs/07_interfaces/openapi_v1.json
docs/release/CHANGELOG.md
docs/schemas/schema_catalog.json
.devpilot/project_state.json
.devpilot/docs_governance/source_registry.json
.devpilot/testing/test_contract_registry.json
.devpilot/testing/test_contract_registry_v2.json
.devpilot/interfaces/api_route_contract_registry.json
.devpilot/interfaces/ui_route_contract_registry.json
ui/web/README.md
ui/web/package.json
```

## 8. Modelo de decision del backlog

POST-H-028 puede cerrar como PASS solo si:

```text
- api_contract_drift_guard_passed = true
- local_auth_cors_hardening_passed = true
- visual_smoke_passed = true
- operator_flows_error_states_passed = true
- ui_route_registry_enforcement_passed = true
- ui_api_hardening_quality_gate_passed = true
- no_remote_execution_enabled = true
- connector_write_enabled = false
- plugin_execution_enabled = false
- external_api_required = false
- forbidden_ui_actions_total = 0
- cors_wildcard_enabled = false
- non_local_bind_allowed = false
```

Debe emitir BLOCK si:

```text
- Existe una ruta API no registrada.
- Existe una ruta registrada que no existe en FastAPI.
- Una ruta protegida no exige token.
- Una ruta protegida no tiene policy binding.
- CORS acepta wildcard.
- API permite host no local sin ADR/backlog especifico.
- UI referencia ruta API no contractada.
- UI lee filesystem o importa core Python.
- UI expone accion critica no permitida.
- Smoke visual no puede renderizar vistas criticas.
- Estados BLOCK/ERROR/401/403/API down no son visibles o testeables.
```

## 9. Micro-sprint POST-H-028-A — API contract drift guard

### Objetivo

Implementar un guard bloqueante contra drift entre FastAPI runtime, OpenAPI, `ApiRouteContractRegistry`, `API_ROUTE_POLICIES` y tests API.

### Justificacion

El repo ya tiene 35 rutas registradas y tests contractuales. POST-H-028-A debe endurecer la regla: ninguna ruta nueva puede aparecer en `/api/v1` sin contrato, policy, response contract, safety flags y tests asociados.

### Alcance

Incluye:

```text
- Crear ApiContractDriftReport schema.
- Comparar rutas FastAPI runtime contra ApiRouteContractRegistry.
- Comparar registry contra docs/07_interfaces/openapi_v1.json si aplica.
- Verificar que rutas no publicas tienen auth_required=true.
- Verificar policy_check_required=true para rutas protegidas.
- Verificar que API_ROUTE_POLICIES cubre rutas protegidas.
- Verificar response_contract=ApplicationResponse donde aplique.
- Detectar rutas mutating sin justificacion local.
- Integrar reporte en api shell-gate o subgate nuevo.
```

No incluye:

```text
- Redisenar API.
- Convertir API local en API publica estable.
- Agregar nuevas rutas funcionales.
```

### Artefactos esperados

```text
docs/schemas/api_contract_drift_report.schema.json
src/devpilot_core/interfaces/api/contract_drift.py
tests/test_post_h_028_api_contract_drift_guard.py
docs/audits/post_h_028_a_api_contract_drift_guard_report.md
docs/post_h_028_a_manifest.json
```

### Criterios PASS

```text
- Drift report valida contra schema.
- Rutas runtime y registry coinciden.
- Rutas registry inexistentes se detectan.
- Ruta protegida sin policy produce BLOCK en fixture.
- Ruta nueva sin contrato produce BLOCK en fixture.
- OpenAPI local no contradice registry en paths criticos.
- No se habilitan remote, connector write, plugin execution ni external APIs.
```

### Criterios BLOCK

```text
- Drift se reporta como warning no bloqueante para rutas protegidas.
- Public paths crecen sin justificacion.
- API_ROUTE_POLICIES puede omitir ruta protegida.
- response mapping deja errores sin ApplicationResponse.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_028_api_contract_drift_guard.py `
  tests/test_post_h_014_api_route_contracts.py `
  tests/test_api_contract.py `
  tests/test_api_local.py `
  tests/test_schema_registry.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core api contract-drift --json
python -m devpilot_core api contract-drift --json --write-report
python -m devpilot_core schema validate --schema-id ApiContractDriftReport --instance outputs/reports/api_contract_drift_report.json --json
```

## 10. Micro-sprint POST-H-028-B — Local auth and CORS hardening

### Objetivo

Endurecer la seguridad local de API/UI: token, CORS, localhost binding, headers, token redaction, settings redacted y pruebas negativas de bypass.

### Justificacion

La API ya bloquea wildcard CORS y host no local. POST-H-028-B debe convertir esa postura en un paquete de hardening con reporte schema-backed y pruebas negativas mas completas, sin introducir auth enterprise.

### Alcance

Incluye:

```text
- Crear LocalApiSecurityHardeningReport schema.
- Probar rutas protegidas sin token: 401/403 esperado.
- Probar token incorrecto: 401/403 esperado.
- Probar token correcto: PASS en rutas permitidas.
- Probar CORS wildcard rechazado.
- Probar origen local permitido.
- Probar origen no local rechazado.
- Probar host 0.0.0.0 bloqueado.
- Probar que DEVPILOT_API_ALLOW_NON_LOCALHOST no habilita nada.
- Verificar security headers.
- Verificar settings/providers sin secretos raw.
- Verificar token redacted en reportes.
```

No incluye:

```text
- OIDC.
- SSO.
- Usuarios enterprise.
- Rotacion persistente de tokens.
- Rate limiting industrial.
```

### Artefactos esperados

```text
docs/schemas/local_api_security_hardening_report.schema.json
src/devpilot_core/interfaces/api/security_hardening.py
tests/test_post_h_028_local_auth_cors_hardening.py
docs/audits/post_h_028_b_local_auth_cors_hardening_report.md
docs/post_h_028_b_manifest.json
```

### Criterios PASS

```text
- Rutas protegidas sin token fallan.
- Rutas protegidas con token invalido fallan.
- Rutas protegidas con token valido pasan si policy permite.
- CORS wildcard permanece false.
- Host no local bloquea.
- Security posture reporta local-only.
- Tokens se redactan en output.
- Settings UI/API no expone secretos raw.
```

### Criterios BLOCK

```text
- Una ruta protegida responde sin token.
- Wildcard CORS es aceptado.
- Host no local se habilita por env var.
- Token se escribe en logs/reportes.
- Settings devuelve secreto raw.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_028_local_auth_cors_hardening.py `
  tests/test_post_h_014_security_hardening.py `
  tests/test_api_security.py `
  tests/test_api_settings.py `
  tests/test_api_approvals_actions.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core api security-hardening --json
python -m devpilot_core api security-hardening --json --write-report
python -m devpilot_core schema validate --schema-id LocalApiSecurityHardeningReport --instance outputs/reports/local_api_security_hardening_report.json --json
```

## 11. Micro-sprint POST-H-028-C — Visual smoke tests

### Objetivo

Agregar pruebas visuales locales para validar que las vistas criticas renderizan correctamente, muestran estados esperados y mantienen la frontera API-only.

### Justificacion

`npm test` actual es dependency-light y contractual. El informe final identifica falta de pruebas visuales reales. POST-H-028-C debe cubrir render visual minimo con screenshots o alternativa equivalente, sin hacer que pytest basal dependa siempre de Node/browser.

### Alcance

Incluye:

```text
- Evaluar Playwright o alternativa local simple.
- Crear UiVisualSmokeReport schema.
- Definir modo opt-in para pruebas browser si Playwright requiere instalacion.
- Capturar o verificar render de Dashboard.
- Verificar Report/Trace Viewer.
- Verificar Approval Center.
- Verificar Settings redacted.
- Verificar Operator Dashboard.
- Verificar estados 401/403/BLOCK/API down/empty.
- Guardar screenshots solo en outputs/ui-smoke o test-results no versionables.
- Mantener npm test actual como smoke contractual ligero.
```

No incluye:

```text
- Cobertura visual exhaustiva.
- Cross-browser industrial.
- Pixel-perfect assertions fragiles.
- Requerir navegador para toda la suite pytest.
```

### Artefactos esperados

```text
docs/schemas/ui_visual_smoke_report.schema.json
ui/web/playwright.config.ts
ui/web/tests/visual-smoke.spec.ts
src/devpilot_core/interfaces/api/visual_smoke_report.py
tests/test_post_h_028_visual_smoke_contract.py
docs/audits/post_h_028_c_visual_smoke_report.md
docs/post_h_028_c_manifest.json
```

### Criterios PASS

```text
- Visual smoke corre localmente en modo documentado.
- Si browser tooling no esta instalado, el core pytest reporta skip/advisory, no falso PASS.
- Al menos cinco vistas criticas renderizan.
- Estados empty/error/BLOCK/unauthorized son visibles.
- Screenshots no se versionan.
- No se introduce dependencia de red externa para test core.
- La UI sigue sin importar Python/core ni leer filesystem.
```

### Criterios BLOCK

```text
- Visual smoke requiere API remota.
- Visual smoke ignora errores 401/403.
- Screenshots se guardan como fuente versionada.
- Prueba visual pasa aunque dashboard este en blanco.
- Se agregan rutas UI sin registry.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_028_visual_smoke_contract.py `
  tests/test_web_ui_mvp.py `
  tests/test_web_ui_report_trace_viewer.py `
  tests/test_web_ui_approval_center.py `
  tests/test_web_ui_settings.py `
  tests/test_post_h_015_operator_dashboard_ui.py `
  -q
npm --prefix ui/web test
```

Si Playwright queda incorporado:

```powershell
npm --prefix ui/web run test:visual
```

### Comandos objetivo

```powershell
python -m devpilot_core api visual-smoke-report --json --write-report
python -m devpilot_core schema validate --schema-id UiVisualSmokeReport --instance outputs/reports/ui_visual_smoke_report.json --json
```

## 12. Micro-sprint POST-H-028-D — Operator flows and error states

### Objetivo

Madurar los flujos operacionales de la UI/API para que el operador entienda estado, errores, bloqueos y acciones siguientes sin leer logs crudos ni codigo.

### Justificacion

La UI ya muestra dashboard, reports, traces, approvals, settings y operator dashboard. POST-H-028-D debe convertirlos en flujos coherentes: API down, token missing, unauthorized, forbidden, empty reports, BLOCK action, approval pending, settings redacted y next actions.

### Alcance

Incluye:

```text
- Crear OperatorFlowSmokeReport schema.
- Definir flujos criticos de operador.
- Verificar API down en UI.
- Verificar token missing/invalid.
- Verificar report list empty state.
- Verificar trace list empty state.
- Verificar security posture redacted.
- Verificar no-go action BLOCK visible.
- Verificar approval create/list/decision flow local cuando aplica.
- Verificar settings providers plan-only/redacted.
- Verificar operator dashboard no-go gates y next actions.
- Agregar mensajes de troubleshooting alineados con runbook.
```

No incluye:

```text
- Wizard completo de onboarding.
- UI para toda la CLI.
- Ejecucion real de acciones sensibles.
- Multiusuario.
```

### Artefactos esperados

```text
docs/schemas/operator_flow_smoke_report.schema.json
src/devpilot_core/interfaces/api/operator_flow_smoke.py
tests/test_post_h_028_operator_flows_error_states.py
docs/audits/post_h_028_d_operator_flows_error_states_report.md
docs/post_h_028_d_manifest.json
```

### Flujos minimos

```text
1. API apagada -> UI muestra conexion fallida con accion sugerida.
2. Token ausente -> UI muestra unauthorized sin filtrar token.
3. Token invalido -> UI muestra 401/403.
4. Dashboard listo -> muestra estado local y no-go gates.
5. Reports vacios -> empty state explicito.
6. Traces vacias -> empty state explicito.
7. Approval Center -> lista/crea/decide en modo permitido.
8. Action Launcher -> readiness/code-review/refactor-plan dry-run.
9. Accion prohibida -> BLOCK visible.
10. Settings -> no secretos raw.
```

### Criterios PASS

```text
- Cada flujo minimo tiene test o smoke report.
- UI no muestra stack traces crudos.
- UI no muestra secretos.
- BLOCK/ERROR/empty/loading son distinguibles.
- Acciones dry-run siguen allowlist.
- Acciones criticas no aparecen como disponibles.
```

### Criterios BLOCK

```text
- UI queda en blanco ante API down.
- UI oculta BLOCK como exito.
- UI permite accion no-go.
- UI muestra token/secreto raw.
- UI sugiere exponer API en 0.0.0.0 como solucion.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_028_operator_flows_error_states.py `
  tests/test_api_reports_traces.py `
  tests/test_api_approvals_actions.py `
  tests/test_api_settings.py `
  tests/test_post_h_015_operator_dashboard_application_api.py `
  tests/test_post_h_015_operator_dashboard_ui.py `
  tests/test_web_ui_mvp.py `
  -q
```

### Comandos objetivo

```powershell
python -m devpilot_core api operator-flow-smoke --json
python -m devpilot_core api operator-flow-smoke --json --write-report
python -m devpilot_core schema validate --schema-id OperatorFlowSmokeReport --instance outputs/reports/operator_flow_smoke_report.json --json
```

## 13. Micro-sprint POST-H-028-E — UI route registry enforcement

### Objetivo

Hacer que `UiRouteContractRegistry` sea enforcement bloqueante para paginas, vistas, componentes de flujo y rutas API consumidas por la UI.

### Justificacion

El repo ya cuenta con `UiRouteContractRegistry` con 5 rutas y tests. POST-H-028-E debe impedir crecimiento no gobernado: una vista nueva, una ruta API nueva consumida por UI o una accion UI nueva debe declararse, clasificarse y probarse.

### Alcance

Incluye:

```text
- Crear UiRouteEnforcementReport schema.
- Escanear UI para vistas/rutas/componentes de pagina.
- Comparar vistas reales contra UiRouteContractRegistry.
- Verificar allowed_api_routes contra ApiRouteContractRegistry.
- Verificar safety flags: local_first, dry_run, no_remote, no_connector_write, no_plugin_execution.
- Verificar estados requeridos: loading, empty, error, block.
- Verificar action allowlist.
- Bloquear rutas peligrosas o acciones sensibles.
- Integrar enforcement en api shell-gate o quality-gate.
```

No incluye:

```text
- Router SPA completo obligatorio.
- Nueva navegacion compleja.
- Expansiones funcionales.
```

### Artefactos esperados

```text
docs/schemas/ui_route_enforcement_report.schema.json
src/devpilot_core/interfaces/api/ui_route_enforcement.py
tests/test_post_h_028_ui_route_registry_enforcement.py
docs/audits/post_h_028_e_ui_route_registry_enforcement_report.md
docs/post_h_028_e_manifest.json
```

### Criterios PASS

```text
- Toda vista critica existente esta registrada.
- Toda allowed_api_route existe en ApiRouteContractRegistry.
- UI route sin required state produce BLOCK.
- UI route con accion prohibida produce BLOCK.
- UI route con filesystem/core import produce BLOCK.
- Enforcement se integra a hardening/industrial.
- Documentacion y TCR quedan sincronizados.
```

### Criterios BLOCK

```text
- Pagina nueva no registrada.
- UI consume endpoint no registrado.
- UI action allowlist contiene patch/apply, rollback/execute, refactor/execute, tests/run, git/push o deploy.
- Registry queda advisory para vistas criticas.
```

### Pruebas focales

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_028_ui_route_registry_enforcement.py `
  tests/test_post_h_014_ui_shell_contract.py `
  tests/test_post_h_014_ui_api_shell_gate.py `
  tests/test_web_ui_mvp.py `
  tests/test_quality_gate.py `
  tests/test_schema_registry.py `
  tests/test_project_global_state.py `
  -q
npm --prefix ui/web test
```

### Comandos objetivo

```powershell
python -m devpilot_core api ui-route-enforcement --json
python -m devpilot_core api ui-route-enforcement --json --write-report
python -m devpilot_core schema validate --schema-id UiRouteEnforcementReport --instance outputs/reports/ui_route_enforcement_report.json --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 14. Quality gate propuesto

Al cierre de POST-H-028-E debe existir un subgate:

```text
ui-api-local-hardening
```

Debe agregarse a:

```text
quality-gate run --profile hardening
quality-gate run --profile industrial
```

Debe verificar:

```text
- ApiContractDriftReport PASS.
- LocalApiSecurityHardeningReport PASS.
- UiVisualSmokeReport PASS o visual tooling pending justificado y no bloqueante solo durante version inicial.
- OperatorFlowSmokeReport PASS.
- UiRouteEnforcementReport PASS.
- api shell-gate PASS.
- npm --prefix ui/web test PASS.
- No forbidden UI actions.
- No CORS wildcard.
- No host remoto.
- No API publica/enterprise claim.
```

## 15. Secuencia recomendada de implementacion

Orden obligatorio:

```text
1. POST-H-028-A — API contract drift guard.
2. POST-H-028-B — Local auth and CORS hardening.
3. POST-H-028-C — Visual smoke tests.
4. POST-H-028-D — Operator flows and error states.
5. POST-H-028-E — UI route registry enforcement.
```

Razon:

```text
- No se debe mejorar UX sobre contratos API con drift.
- No se debe ampliar visual smoke sin seguridad local reforzada.
- No se deben madurar flujos de operador sin estados visuales testeables.
- No se debe cerrar la ola sin enforcement de rutas UI.
```

## 16. Validacion focal recomendada por micro-sprint

Validacion base:

```powershell
$env:PYTHONPATH="src"

python -m devpilot_core project-state validate --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core schema list --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core api shell-gate --json --write-report
python -m devpilot_core schema validate --schema-id UiApiShellReport --instance outputs/reports/ui_api_shell_report.json --json
npm --prefix ui/web test
```

Validacion focal acumulativa POST-H-028:

```powershell
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_028_api_contract_drift_guard.py `
  tests/test_post_h_028_local_auth_cors_hardening.py `
  tests/test_post_h_028_visual_smoke_contract.py `
  tests/test_post_h_028_operator_flows_error_states.py `
  tests/test_post_h_028_ui_route_registry_enforcement.py `
  tests/test_post_h_014_api_route_contracts.py `
  tests/test_post_h_014_security_hardening.py `
  tests/test_post_h_014_ui_api_shell_gate.py `
  tests/test_post_h_014_ui_shell_contract.py `
  tests/test_api_contract.py `
  tests/test_api_local.py `
  tests/test_api_security.py `
  tests/test_api_reports_traces.py `
  tests/test_api_settings.py `
  tests/test_api_approvals_actions.py `
  tests/test_web_ui_mvp.py `
  tests/test_web_ui_report_trace_viewer.py `
  tests/test_web_ui_approval_center.py `
  tests/test_web_ui_settings.py `
  tests/test_post_h_015_operator_dashboard_application_api.py `
  tests/test_post_h_015_operator_dashboard_ui.py `
  tests/test_quality_gate.py `
  tests/test_schema_registry.py `
  tests/test_project_global_state.py `
  -q
```

Validacion final opcional de cierre:

```powershell
python -m pytest -q
```

La suite completa debe reservarse para cierre de backlog o regresion amplia.

## 17. Cierre industrial del backlog

POST-H-028 solo puede cerrarse si:

```text
- Los cinco micro-sprints estan implementados, probados y documentados.
- ui-api-local-hardening existe y pasa en hardening/industrial.
- api shell-gate sigue pasando.
- npm --prefix ui/web test pasa.
- Drift API esta bloqueado.
- Auth/CORS/local bind estan bloqueados contra bypass.
- Visual smoke cubre vistas criticas o declara limites transitorios aceptados.
- Operator flows muestran estados BLOCK/ERROR/empty/loading.
- UI route registry enforcement bloquea crecimiento no gobernado.
- README, runbook, UI/API runbook, docs/07_interfaces, changelog, source registry, TCR y project_state estan sincronizados.
```

## 18. Riesgos y mitigaciones

| Riesgo | Severidad | Mitigacion en POST-H-028 |
|---|---:|---|
| Ruta API no contractada | Alta | API contract drift guard |
| Token bypass | Alta | Local auth negative tests |
| CORS wildcard | Alta | Security hardening report bloqueante |
| Host no local | Alta | Bind guard y no-go test |
| UI expone accion critica | Alta | UI route enforcement y action allowlist |
| UI muestra secreto/token | Alta | Settings redaction tests |
| Visual smoke fragil | Media | Assertions estructurales y screenshots solo como evidencia |
| Node/browser hace flakey pytest core | Media | Visual tests opt-in o profile controlado |
| UI parece enterprise | Media | Claims y runbook aclaran local-only/no multiuser |
| UI intenta replicar CLI | Media/alta | Scope rule: operador/evidencia, no batch/sensible |

## 19. Instrucciones de almacenamiento en el repo

Ruta canonica recomendada dentro de `repo_DevPilot_Local_262_POST_H_025_E`:

```text
docs/backlogs/POST-H-028_ui_api_local_hardening.md
```

Ruta Windows equivalente:

```powershell
D:\Projects\DevPilot_Local\docs\backlogs\POST-H-028_ui_api_local_hardening.md
```

Si se mantiene la convencion de documento top-level por hito, crear tambien durante POST-H-028-A:

```text
docs/POST-H-028_ui_api_local_hardening.md
```

Ese documento top-level no debe divergir del backlog canonico. Si se crea, registrarlo en:

```text
.devpilot/docs_governance/source_registry.json
README.md
docs/05_operations/runbook.md
docs/release/CHANGELOG.md
```

## 20. Git sugerido para incorporar este backlog

Cuando se copie este archivo al repo:

```bash
git add docs/backlogs/POST-H-028_ui_api_local_hardening.md
git commit -m "Add POST-H-028 UI API local hardening backlog"
```

Si tambien se agrega documento top-level o source registry:

```bash
git add docs/backlogs/POST-H-028_ui_api_local_hardening.md docs/POST-H-028_ui_api_local_hardening.md .devpilot/docs_governance/source_registry.json README.md docs/05_operations/runbook.md docs/release/CHANGELOG.md
git commit -m "Register POST-H-028 UI API local hardening backlog"
```

## 21. Decision de alcance

POST-H-028 es una ola de hardening operacional UI/API local.

La linea de corte es:

```text
Permitido: contratos, seguridad local, visual smoke, flujos de operador, enforcement de rutas, reportes y documentacion.
No permitido: enterprise auth, API publica, SaaS, remote, connector write, plugin execution, ejecucion critica desde UI, replicar toda la CLI.
```

La siguiente ola, POST-H-029, debe usar esta UI/API mas estable para mejorar testing tiers, impacto y costo de regresion sin sobrecargar al operador.


## Implementacion POST-H-028-B — Local auth and CORS hardening

Estado: `implemented-initial`.

POST-H-028-B agrega un hardening local schema-backed para la seguridad API/UI. El comando principal es:

```powershell
python -m devpilot_core api security-hardening --json --write-report
```

El runner `LocalApiSecurityHardeningRunner` verifica token obligatorio en rutas protegidas, bloqueo de token invalido, PASS con token valido, CORS restringido a localhost/loopback, rechazo de wildcard, rechazo de origen no local, bloqueo de `0.0.0.0` incluso con `DEVPILOT_API_ALLOW_NON_LOCALHOST`, headers de seguridad y redaccion de settings/providers y token en reportes.

Limites explicitos: no implementa OIDC, SSO, IAM enterprise, rate limiting industrial, TLS/mTLS activo, API publica remota ni sesiones persistentes. Es una primera version local robusta que prepara POST-H-028-C/D/E.

Artefactos:

```text
docs/schemas/local_api_security_hardening_report.schema.json
src/devpilot_core/interfaces/api/security_hardening.py
tests/test_post_h_028_local_auth_cors_hardening.py
docs/audits/post_h_028_b_local_auth_cors_hardening_report.md
docs/post_h_028_b_manifest.json
```
