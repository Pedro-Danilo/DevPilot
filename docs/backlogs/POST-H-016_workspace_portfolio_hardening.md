---

doc_id: "POST-H-016-BACKLOG"
id: "POST-H-016"
title: "POST-H-016 — Workspace portfolio hardening"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
updated: "2026-06-29"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P2"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "in_progress"
current_micro_sprint: "POST-H-016-B"
next_micro_sprint: "POST-H-016-C"
---

# POST-H-016 — Workspace portfolio hardening

## 1. Objetivo

Endurecer la gestión de **múltiples workspaces locales** y el portfolio local de DevPilot, garantizando aislamiento, registro explícito, selección segura, estado read-only por defecto y prevención de contaminación entre proyectos.

El objetivo no es crear multi-tenant ni SaaS. El objetivo es que un operador local pueda gestionar varios proyectos DevPilot sin mezclar estado, secretos, trazas, reports, approvals o configuraciones.

## 2. Contexto y justificación

DevPilot ya tiene capacidades iniciales:

```text
src/devpilot_core/workspace/manager.py
src/devpilot_core/workspace/registry.py
src/devpilot_core/portfolio/status.py
.devpilot/workspaces/workspace_registry.json
workspace list/register/select/registry-validate
portfolio status
```

Pero la madurez actual es `implemented-initial`. Los riesgos principales son:

```text
- Usar workspace equivocado por discovery ambiguo.
- Leer o escribir estado en workspace no activo.
- Compartir secretos accidentalmente entre workspaces.
- Mezclar outputs/reports/traces de distintos proyectos.
- Selección de workspace sin auditoría.
- Portfolio status sobre workspaces no registrados.
- Falta de policy explícita para deny_unregistered_workspaces.
```

## 3. Alcance

Incluye:

```text
- Workspace registry v2.
- Política de aislamiento de workspaces.
- Validación de workspace activo.
- Portfolio status read-only robusto.
- Reporte de contaminación cruzada.
- Tests de path isolation y registry semantics.
- Integración con PolicyEngine/PathGuard.
```

No incluye:

```text
- Workspaces remotos.
- Sincronización cloud.
- Multiusuario enterprise.
- Compartir secretos entre workspaces.
- Cross-workspace writes.
- Ejecución distribuida.
```

## 4. Fuentes de entrada obligatorias

```text
src/devpilot_core/workspace/manager.py
src/devpilot_core/workspace/registry.py
src/devpilot_core/portfolio/status.py
src/devpilot_core/policy/path_guard.py
docs/schemas/workspace_project.schema.json
docs/schemas/multiworkspace_registry.schema.json
.devpilot/workspaces/workspace_registry.json
docs/05_operations/runbook.md
docs/backlogs/post_h_prioritized_roadmap.md
tests/test_workspace_manager.py
tests/test_multiworkspace.py
```

## 5. Entregables

```text
docs/schemas/multiworkspace_registry_v2.schema.json
docs/schemas/workspace_isolation_report.schema.json
.devpilot/workspaces/workspace_registry.json              # migrado compatible
src/devpilot_core/workspace/registry_v2.py
src/devpilot_core/workspace/isolation.py
src/devpilot_core/portfolio/hardening.py
tests/test_post_h_016_workspace_registry_v2.py
tests/test_post_h_016_workspace_isolation.py
tests/test_post_h_016_portfolio_hardening.py
docs/05_operations/workspace_portfolio_runbook.md
outputs/reports/workspace_isolation_report.json           # generado, no versionable
```

Actualizar:

```text
src/devpilot_core/cli.py o cli_registry cuando exista
src/devpilot_core/policy/path_guard.py
src/devpilot_core/quality/gate.py
docs/schemas/schema_catalog.json
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

### 6.1 Workspace registry v2

```json
{
  "schema_version": "2.0",
  "active_workspace_id": "devpilot-local",
  "defaults": {
    "deny_unregistered_workspaces": true,
    "cross_workspace_state_reads": false,
    "cross_workspace_writes": false,
    "secret_sharing_allowed": false,
    "portfolio_status_read_only": true
  },
  "workspaces": [
    {
      "workspace_id": "devpilot-local",
      "root_path": ".",
      "project_file": ".devpilot/project.yaml",
      "state_path": ".devpilot/devpilot.db",
      "status": "active",
      "risk_level": "medium",
      "registered_at_utc": "2026-06-23T00:00:00Z",
      "last_validated_at_utc": null
    }
  ],
  "security": {
    "network_used": false,
    "external_api_used": false,
    "remote_execution_used": false,
    "mutations_performed": false,
    "secrets_read": false
  }
}
```

### 6.2 Isolation report

```text
workspace_id
root_path
is_registered
is_active
project_file_exists
path_guard_root
state_path_inside_workspace
outputs_inside_workspace
traces_inside_workspace
secrets_shared_detected
cross_workspace_refs_detected
findings
```

## 7. Principios

```text
1. Registered-first: solo workspaces registrados pueden aparecer en portfolio.
2. Active workspace explicit: toda operación sensible debe saber workspace activo.
3. No cross-state: estado, secrets, traces y reports no se comparten.
4. Read-only portfolio: portfolio status no muta proyectos.
5. PathGuard alignment: workspace root es frontera de seguridad.
6. Repair is plan-first: no auto-repair destructivo.
```

## 8. Micro-sprints propuestos

### POST-H-016-A — Registry v2 y migración compatible

Tareas:

```text
1. Crear multiworkspace_registry_v2.schema.json.
2. Implementar migración read-only v1 → v2.
3. Mantener compatibilidad con schema actual.
4. Agregar registry-validate v2.
5. Crear tests.
```

PASS:

```text
PASS si registry v1 vigente se interpreta correctamente.
PASS si v2 exige deny_unregistered_workspaces=true.
PASS si no hay mutaciones por defecto.
```

BLOCK:

```text
BLOCK si secret_sharing_allowed=true por defecto.
BLOCK si cross_workspace_writes=true.
```

### POST-H-016-B — Workspace isolation validator

Tareas:

```text
1. Implementar isolation.py.
2. Validar root/state/outputs/traces dentro del workspace.
3. Detectar referencias cruzadas a otros roots registrados.
4. Integrar PathGuard.
5. Generar workspace_isolation_report.json.
```

PASS:

```text
PASS si detecta state_path fuera del root.
PASS si detecta outputs/traces fuera del root.
PASS si no lee secretos.
```

### POST-H-016-C — Portfolio status hardening

Tareas:

```text
1. Endurecer portfolio status.
2. Mostrar solo workspaces registrados.
3. Agregar summary por workspace: readiness, state, reports, risks.
4. Reportar unknown en fuentes ausentes.
5. Evitar cross-workspace writes.
```

PASS:

```text
PASS si portfolio status es read-only.
PASS si workspaces no registrados se bloquean o se reportan como denied.
```

### POST-H-016-D — CLI/API integration segura

Tareas:

```text
1. Actualizar comandos workspace list/register/select/registry-validate.
2. Exponer portfolio read-only por ApplicationService.
3. Validar que API no cambia active workspace sin operación explícita futura.
4. Crear tests de boundary.
```

PASS:

```text
PASS si selección de workspace queda auditada.
PASS si no hay writes cross-workspace desde API.
```

### POST-H-016-E — Quality gate y runbook

Tareas:

```text
1. Agregar subgate workspace-portfolio-hardening.
2. Documentar operación multiworkspace.
3. Actualizar test contract registry.
4. Crear checklist de onboarding de workspace.
```

PASS:

```text
PASS si quality gate falla ante registry inválido.
PASS si runbook explica selección, validación y límites.
```

## 9. Comandos esperados

```powershell
python -m devpilot_core workspace registry-validate --json
python -m devpilot_core workspace isolation-check --json --write-report
python -m devpilot_core portfolio status --json --write-report
python -m pytest tests/test_post_h_016_workspace_registry_v2.py -q
python -m pytest tests/test_post_h_016_workspace_isolation.py -q
python -m pytest tests/test_post_h_016_portfolio_hardening.py -q
python -m devpilot_core quality-gate run --profile hardening --json
```

## 10. Criterios BLOCK

```text
BLOCK si un workspace no registrado puede ser operado como activo.
BLOCK si cross_workspace_writes=true.
BLOCK si secret_sharing_allowed=true.
BLOCK si PathGuard root no coincide con workspace root.
BLOCK si portfolio status muta estado.
```

## 11. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Operar sobre proyecto equivocado | Alta | Active workspace explícito y reportado. |
| Contaminación de estados | Alta | Isolation validator. |
| Secret sharing accidental | Alta | Deny-by-default y checks. |
| Compatibilidad rota con registry actual | Media | Migración compatible v1/v2. |

## 12. Definition of Done

```text
[ ] Registry v2 validado.
[ ] Isolation report implementado.
[ ] Portfolio status read-only endurecido.
[ ] PathGuard alineado con workspace root.
[ ] Quality gate integrado.
[ ] Runbook aprobado.
```
