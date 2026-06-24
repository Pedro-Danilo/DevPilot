---
title: "POST-H-002-E — Quality gate y documentación"
doc_id: "POST-H-002-E-AUDIT"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
approval: "internal"
updated: "2026-06-24"
---

# POST-H-002-E — Quality gate y documentación

## Propósito

`POST-H-002-E` conecta el dashboard local de madurez con los gates de calidad de DevPilot sin reemplazar los gates existentes. El micro-sprint cierra el hito `POST-H-002` con prueba documental, contrato de test, quality gate específico y documentación operativa sincronizada.

## Estado

Estado: `implemented-initial`. El hito padre `POST-H-002` queda cerrado como dashboard local operativo basado en evidencia post-H, pero la capacidad sigue siendo local/read-only y preliminar para producción industrial completa.

## Alcance implementado

```text
- Gate `MaturityDashboardQualityGate`.
- ApplicationService `maturity_dashboard_gate()`.
- CLI `python -m devpilot_core maturity gate --json`.
- Inclusión del subgate `maturity-dashboard` en `quality-gate run --profile hardening` e `industrial`.
- Alias CLI `schema validate --schema-id` para alinear comandos del backlog.
- Test contract v1 `post-h-002-maturity-dashboard`.
- Prueba documental `tests/test_post_h_002_documentation.py`.
- Cierre documental de README, runbook, changelog, backlog y project_state.
```

## Funcionamiento

El gate ejecuta el dashboard por la frontera `ApplicationService`, valida el payload contra `MaturityDashboard`, verifica umbrales mínimos de cierre, confirma no-go gates de remote/connectors/plugins, comprueba evidencia por capacidad y valida alineación con roadmap post-H. Si se invoca con `--write-report`, persiste y valida `outputs/reports/maturity_dashboard.json` y `outputs/reports/maturity_dashboard.md`.

## Integración dentro de DevPilot

```text
CLI maturity gate
→ ApplicationService.maturity_dashboard_gate()
→ MaturityApplicationService.dashboard_gate()
→ MaturityDashboardQualityGate
→ MaturityApplicationService.dashboard()
→ MaturityDashboardBuilder
→ SchemaValidator
→ CommandResult
```

El `quality-gate hardening` consume el gate como subgate adicional, pero no modifica fuentes ni ejecuta pytest implícitamente.

## Criterios PASS

```text
PASS si `maturity gate --json` retorna ok=true.
PASS si el dashboard valida contra schema.
PASS si remote_execution_enabled=false.
PASS si connector_write_enabled=false.
PASS si plugin_execution_enabled=false.
PASS si external_apis_enabled_by_default=false.
PASS si las capacidades no-go SEC-001, SEC-002 y SEC-003 están blocked.
PASS si test-contracts validate pasa.
PASS si quality-gate hardening sigue PASS.
PASS si project-state validate pasa con POST-H-002 cerrado y POST-H-003 como siguiente hito.
```

## Criterios BLOCK

```text
BLOCK si el dashboard inventa madurez sin source_evidence.
BLOCK si el schema MaturityDashboard falla.
BLOCK si se habilita remote execution, connector write, plugin execution o APIs externas.
BLOCK si `--write-report` escribe fuera de outputs/reports.
BLOCK si se declara production-ready completo, enterprise-ready, remote-ready o compliance-certified.
BLOCK si el hardening gate pierde coherencia.
```

## Riesgos y limitaciones

El dashboard de madurez no equivale a declaración `production-ready-local`. Esa declaración queda reservada para `POST-H-025`. El dashboard no reemplaza `industrial-readiness`, `test-contracts`, `project-state` ni `quality-gate`; los consume y los hace visibles como evidencia local.

## Comandos de validación

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_post_h_002_maturity_dashboard.py -q
python -m pytest tests/test_schema_registry.py tests/test_application_services.py tests/test_quality_gate.py tests/test_test_contract_registry.py tests/test_project_global_state.py tests/test_post_h_002_documentation.py tests/test_post_h_002_maturity_dashboard.py -q
python -m devpilot_core maturity dashboard --json --write-report
python -m devpilot_core maturity gate --json --write-report
python -m devpilot_core schema validate --schema-id MaturityDashboard --instance outputs/reports/maturity_dashboard.json --json
python -m devpilot_core validate docs --json
python -m devpilot_core project-state validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## No-go gates

```text
No remote execution.
No connector write.
No plugin execution.
No APIs externas por defecto.
No source mutations desde el gate.
No producción completa.
No claims enterprise/compliance/remote.
```

## Próximo paso

El siguiente hito recomendado por el roadmap definitivo es `POST-H-003 — Test Contract Registry 2.0`.
