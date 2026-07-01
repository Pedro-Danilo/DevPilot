---

doc_id: "POST-H-021-BACKLOG"
id: "POST-H-021"
title: "POST-H-021 — Remote Runner ADR-2"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-01"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P3"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "active"
current_micro_sprint: "POST-H-021-A"
next_micro_sprint: "POST-H-021-B"
---

# POST-H-021 — Remote Runner ADR-2

## 0. Estado de implementación

Estado del backlog: `approved / active`.

Micro-sprint actual: `POST-H-021-A — Inventario remote y baseline de bloqueo`.

Resultado POST-H-021-A: `implemented-initial`. Se inventaría `src/devpilot_core/remote/`, `.devpilot/remote/runner_registry.json` y `docs/schemas/remote_runner.schema.json`; se agrega `docs/schemas/remote_readiness_criteria.schema.json`, `.devpilot/remote/remote_readiness_criteria.json`, `tests/test_post_h_021_remote_disabled_invariants.py`, `docs/audits/post_h_021_a_remote_inventory_baseline_report.md` y `docs/post_h_021_a_manifest.json`.

El baseline confirma que remote runner sigue bloqueado: `remote_execution_allowed=false`, `remote_runner_enabled=false`, `execution_allowed=false`, `network_used=false`, `external_api_used=false`, `credentials_required=false`, `secrets_read=false` y `requires_future_adr=true`.

Siguiente micro-sprint: `POST-H-021-B — ADR-2 de Remote Runner`.

## 1. Objetivo

Elaborar una **ADR-2 de Remote Runner** que defina, sin implementar ejecución remota activa, las condiciones técnicas, de seguridad, gobernanza, operación y evidencias necesarias para que DevPilot pueda evaluar en el futuro si procede o no abrir una capacidad de remote runner.

Este backlog no habilita remote execution. Su producto final es una decisión arquitectónica verificable, un modelo de no-go gates, un inventario de riesgos, un contrato de readiness y un conjunto de pruebas que garanticen que la funcionalidad remota permanece bloqueada mientras no se cumplan condiciones industriales estrictas.

## 2. Contexto y justificación

DevPilot cuenta con `src/devpilot_core/remote/` y `.devpilot/remote/` como baseline experimental/stub. El roadmap definitivo mantiene remote/enterprise en una oleada de diseño, no de ejecución. El riesgo central es que la existencia de un registry o de un stub sea confundida con permiso para ejecutar procesos fuera del workspace local.

La ADR-2 debe convertir esa frontera en una decisión explícita:

```text
remote registry existe ≠ remote runner habilitado
remote readiness existe ≠ remote execution permitido
remote design existe ≠ transport seguro implementado
```

## 3. Alcance

Incluye:

```text
- Inventario del estado actual de remote runner.
- ADR-2 con alternativas, decisión, consecuencias y no-go gates.
- Remote readiness criteria schema.
- Matriz de riesgos y controles mínimos para remote runner futuro.
- Validator de invariantes: remote execution debe seguir deshabilitado.
- Reporte local de remote readiness en modo read-only.
- Tests de regresión que bloqueen activaciones accidentales.
- Actualización documental del runbook y arquitectura.
```

No incluye:

```text
- Ejecución remota real.
- Agentes remotos.
- Secure transport implementado.
- SSH, HTTP remote, gRPC, websockets productivos o túneles.
- Credenciales remotas.
- Deploy remoto.
- Workers remotos.
- Background jobs remotos.
- Connector write.
- Plugin execution.
```

## 4. Fuentes de entrada obligatorias

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/adr/ADR-POSTH-001-local-first-before-remote.md
docs/03_security/post_h_security_risk_register.md
docs/02_architecture/post_h_current_architecture_map.md
docs/05_operations/runbook.md
src/devpilot_core/remote/
.devpilot/remote/
src/devpilot_core/policy/
src/devpilot_core/identity/
src/devpilot_core/approval/
src/devpilot_core/observability/
.devpilot/testing/test_contract_registry.json
```

## 5. Entregables

```text
docs/adr/ADR-POSTH-004-remote-runner-adr2.md
docs/schemas/remote_readiness_criteria.schema.json
docs/schemas/remote_readiness_report.schema.json
.devpilot/remote/remote_readiness_criteria.json
src/devpilot_core/remote/readiness.py
src/devpilot_core/remote/reports.py
tests/test_post_h_021_remote_adr2.py
tests/test_post_h_021_remote_disabled_invariants.py
docs/05_operations/remote_runner_design_runbook.md
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/cli.py o command registry futuro
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

### 6.1 Remote readiness criteria

```json
{
  "schema_version": "1.0",
  "remote_execution_allowed": false,
  "decision_status": "design-only",
  "requires_future_adr": true,
  "required_before_enablement": [
    "enterprise_deployment_threat_model",
    "secure_transport_design",
    "approval_rbac_hardening",
    "observability_retention",
    "runtime_state_lifecycle_policy",
    "test_contract_registry_2"
  ],
  "no_go_gates": {
    "remote_runner_enabled": false,
    "remote_execution_used": false,
    "network_required": false,
    "external_api_required": false,
    "secrets_required": false,
    "mutations_performed": false
  }
}
```

### 6.2 Remote readiness report

```json
{
  "schema_version": "1.0",
  "ok": true,
  "remote_runner_enabled": false,
  "remote_execution_used": false,
  "decision_status": "design-only",
  "future_adr_required": true,
  "blocking_findings_total": 0,
  "readiness_level": "remote-design-only"
}
```

## 7. Principios de diseño

```text
1. Local-first before remote.
2. Remote design is not remote enablement.
3. Remote runner remains disabled unless a future ADR explicitly changes this.
4. No secrets are required for POST-H-021.
5. No transport implementation is allowed in POST-H-021.
6. Any future remote runner must require RBAC, approval, sandboxing and observability.
7. Any future remote runner must produce auditable evidence.
8. Any future remote runner must support dry-run and kill-switch semantics.
9. Remote execution must remain a BLOCK condition in quality gates until formally approved.
10. The ADR must describe consequences and rejected alternatives.
```

## 8. Micro-sprints propuestos

### POST-H-021-A — Inventario remote y baseline de bloqueo

Objetivo: inventariar el estado real de remote runner y declarar invariantes de bloqueo.

Tareas:

```text
1. Inspeccionar src/devpilot_core/remote/ y .devpilot/remote/.
2. Documentar capacidades reales, stubs y riesgos.
3. Crear remote_readiness_criteria.schema.json.
4. Crear .devpilot/remote/remote_readiness_criteria.json.
5. Crear pruebas que fallen si remote_runner_enabled=true.
6. Confirmar que no hay red ni ejecución remota.
```

Entregables:

```text
docs/schemas/remote_readiness_criteria.schema.json
.devpilot/remote/remote_readiness_criteria.json
tests/test_post_h_021_remote_disabled_invariants.py
```

Criterios PASS:

```text
- El schema valida.
- El criteria file declara remote_execution_allowed=false.
- Las pruebas bloquean activación accidental.
```

Criterios BLOCK:

```text
- Se habilita ejecución remota.
- Se agregan credenciales remotas.
- Se requiere red para validar.
```

### POST-H-021-B — ADR-2 de Remote Runner

Objetivo: crear la decisión arquitectónica formal.

Tareas:

```text
1. Crear ADR-POSTH-004-remote-runner-adr2.md.
2. Incluir contexto, opciones evaluadas, decisión y consecuencias.
3. Documentar alternativas rechazadas: enable-now, SSH ad hoc, connector-as-runner, plugin-as-runner.
4. Definir condiciones mínimas de habilitación futura.
5. Referenciar POST-H-022 y POST-H-023 como prerrequisitos de diseño.
```

Entregables:

```text
docs/adr/ADR-POSTH-004-remote-runner-adr2.md
```

Criterios PASS:

```text
- ADR en status approved/reviewed según política documental.
- La decisión mantiene remote execution disabled.
- Los prerrequisitos futuros son explícitos.
```

Criterios BLOCK:

```text
- La ADR autoriza ejecución remota inmediata.
- La ADR omite RBAC, approval, sandbox u observabilidad.
```

### POST-H-021-C — Remote readiness report read-only

Objetivo: implementar reporte local de readiness sin ejecución remota.

Tareas:

```text
1. Crear src/devpilot_core/remote/readiness.py.
2. Crear src/devpilot_core/remote/reports.py.
3. Leer criteria y runner registry sin mutar estado.
4. Producir RemoteReadinessReport.
5. Exponer CLI read-only: remote runner readiness --json.
```

Entregables:

```text
src/devpilot_core/remote/readiness.py
src/devpilot_core/remote/reports.py
docs/schemas/remote_readiness_report.schema.json
```

Criterios PASS:

```text
- El reporte se genera sin red.
- El reporte confirma remote_runner_enabled=false.
- El reporte no requiere secrets.
```

Criterios BLOCK:

```text
- Se ejecuta un comando remoto.
- Se abre socket o transporte real.
```

### POST-H-021-D — Quality gate de remote disabled

Objetivo: integrar invariantes remote al quality gate.

Tareas:

```text
1. Añadir subgate remote-readiness-design-only.
2. Validar criteria/report/schema.
3. Añadir test contract.
4. Documentar señales PASS/BLOCK.
```

Entregables:

```text
tests/test_post_h_021_remote_adr2.py
.devpilot/testing/test_contract_registry.json actualizado
```

Criterios PASS:

```text
- quality-gate hardening confirma remote disabled.
- test-contracts validate pasa.
```

Criterios BLOCK:

```text
- Cualquier flag remoto activo pasa inadvertido.
```

### POST-H-021-E — Runbook y cierre

Objetivo: cerrar el hito con documentación operacional.

Tareas:

```text
1. Crear remote_runner_design_runbook.md.
2. Documentar cómo interpretar design-only.
3. Agregar checklist de go/no-go futuro.
4. Actualizar changelog y manifest si aplica.
5. Ejecutar validación focal y regresión recomendada.
```

Entregables:

```text
docs/05_operations/remote_runner_design_runbook.md
```

## 9. Comandos de validación esperados

```powershell
python -m pytest tests/test_post_h_021_remote_adr2.py tests/test_post_h_021_remote_disabled_invariants.py -q
python -m devpilot_core schema validate --schema-id RemoteRunnerRegistry --instance .devpilot/remote/runner_registry.json --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
```

## 10. No-go gates

```text
- remote_runner_enabled=true
- remote_execution_used=true
- network_used=true sin ADR futura
- external_api_used=true
- secrets_required=true
- connector_write_enabled=true
- plugin_execution_enabled=true
- claims enterprise production-ready
```

## 11. Riesgos

| Riesgo | Nivel | Mitigación |
|---|---:|---|
| Interpretar ADR como permiso de implementación | Crítico | Texto explícito design-only y tests de bloqueo. |
| Activación accidental de remote runner | Crítico | Invariant tests y quality gate. |
| Saltar threat model | Alto | POST-H-022 como prerrequisito. |
| Saltar secure transport design | Alto | POST-H-023 como prerrequisito. |
| Exposición de secrets | Alto | SecretGuard y no secrets policy. |

## 12. Definition of Done

```text
[ ] ADR-2 creada y validada.
[ ] Remote readiness criteria creado y validado.
[ ] Remote readiness report implementado read-only.
[ ] Quality gate bloquea remote enablement.
[ ] Tests focales pasan.
[ ] No se habilita ejecución remota.
[ ] No se usan APIs externas.
[ ] No se introducen secrets.
```
