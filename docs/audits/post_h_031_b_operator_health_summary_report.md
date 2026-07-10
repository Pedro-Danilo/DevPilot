---
doc_id: POST-H-031-B-OPERATOR-HEALTH-SUMMARY-REPORT
title: "POST-H-031-B - Operator health summary report"
status: approved
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-10"
approval: approved
---

# POST-H-031-B - Operator health summary report

## 1. Decisión

`POST-H-031-B — Operator health summary` queda implementado como `implemented-initial/local-first`.

La implementación agrega una vista operacional de salud para operador basada en `EvidenceGraph`, project state, TCR, documentación gobernada, claims/no-go gates y evidencia runtime regenerable.

## 2. Implementado

- Schema `OperatorHealthSummary` en `docs/schemas/operator_health_summary.schema.json`.
- Configuración `.devpilot/operator/operator_health_config.json`.
- Módulo `src/devpilot_core/evidence_graph/health.py`.
- Método `ApplicationService.operator_health_summary(...)`.
- Operación `operator.health` en `ApplicationService.handle(...)`.
- Comando CLI `python -m devpilot_core evidence health --json`.
- Ruta local protegida `GET /api/v1/operator/health`.
- Registro de schema catalog, documentación, TCR v1/v2, CLI ownership matrix y API route contract registry.
- Pruebas focales `tests/test_post_h_031_operator_health_summary.py`.

## 3. Implementado inicial

La salud operacional se clasifica con semáforo controlado:

- `green`: sin gaps bloqueantes ni warnings relevantes.
- `yellow`: evidencia runtime opcional no regenerada o warnings no bloqueantes.
- `red`: blocking gaps, no-go violation, forbidden claim disponible o fallo bloqueante del grafo.
- `unknown`: evidencia no disponible.
- `not_applicable`: capacidad fuera de alcance.

La primera versión produce `top_actions` para evidencia runtime faltante, pero el mapeo completo gap-to-action queda reservado para `POST-H-031-C`.

## 4. Parcial / pendiente

- `POST-H-031-C` debe implementar reglas completas `GapActionMap`.
- `POST-H-031-D` debe consolidar claims/no-go dashboard.
- `POST-H-031-E` debe implementar UX de export redactado de evidencia.
- La UI puede consumir la ruta API futura, pero este micro-sprint no implementa componentes visuales nuevos.

## 5. Contratos y criterios PASS/BLOCK

### PASS

- El summary valida contra schema.
- Los estados son derivados de evidencia, no hardcodeados como green.
- Gaps bloqueantes se reflejan en salud global red/BLOCK.
- Claims prohibidos no aparecen como capacidades disponibles.
- Output JSON es estable y compatible con `CommandResult`/`ApplicationResponse`.
- Report writing es explícito y limitado a `outputs/reports`.
- ApplicationService expone `operator.health` sin que API/UI importen internals.

### BLOCK

- Salud global green con blocking gaps.
- Claims prohibidos marcados como disponibles.
- Estado derivado de texto libre no validado.
- Lectura obligatoria de outputs inexistentes.
- Mutación no solicitada.
- Comandos recomendados ejecutados automáticamente.
- Lectura de secretos, `.env`, payloads crudos o `.devpilot/devpilot.db`.

## 6. Seguridad

La implementación conserva:

```text
local_first=true
read_only=true
dry_run=true
network_used=false
external_api_used=false
commands_executed=false
secrets_read=false
devpilot_db_read=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## 7. Comandos de verificación

```powershell
$env:PYTHONPATH="src"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest -p no:ddtrace --assert=plain tests/test_post_h_031_operator_health_summary.py -q
python -m devpilot_core evidence health --json
python -m devpilot_core evidence health --json --write-report
python -m devpilot_core schema validate --schema-id OperatorHealthSummary --instance outputs/reports/operator_health_summary.json --json
```

Verificación focal recomendada:

```powershell
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_031_operator_health_summary.py `
  tests/test_post_h_031_evidence_graph_model.py `
  tests/test_post_h_015_operator_dashboard_application_api.py `
  tests/test_schema_registry.py `
  tests/test_test_contract_registry.py `
  tests/test_test_contract_registry_v2.py `
  tests/test_documentation_governance_validator.py `
  tests/test_documentation_source_registry_schema.py `
  tests/test_project_global_state.py `
  -q
```

## 8. Riesgos y limitaciones

- El summary es una vista operator-facing, no una declaración formal de readiness.
- `top_actions` no reemplaza el futuro `GapActionMap`.
- Runtime outputs faltantes pueden producir estado `yellow` sin bloquear el micro-sprint.
- La ruta API queda protegida por token/policy local; no se habilita UI nueva en este sprint.

## 9. Próximo paso

`POST-H-031-C — Gap-to-action mapping`.
