---

doc_id: "POST-H-019-IMPLEMENTATION"
id: "POST-H-019"
title: "POST-H-019 — Plugin sandbox design implementation"
status: "approved"
version: "0.5.0"
owner: "Ordóñez"
updated: "2026-06-30"
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
implementation_status: "active"
current_micro_sprint: "POST-H-019-D"
next_micro_sprint: "POST-H-019-E"
---

# POST-H-019 — Plugin sandbox design sin ejecución arbitraria

## 0. Estado de implementación

Estado del backlog: `approved / active`.

Micro-sprint actual: `POST-H-019-D — Quality gate plugin safety`.

Resultado POST-H-019-A: `implemented-initial`. Se aprueba el backlog para implementación y se agregan el threat model y el diseño arquitectónico metadata-only del sandbox de plugins. No se habilita ejecución de plugins, `importlib`, `subprocess`, red, APIs externas, marketplace ni instalación de dependencias.

Resultado POST-H-019-B: `implemented-initial`. Se agrega `PluginPermissionModel`, schema `PluginPermissionModel`, `.devpilot/plugins/plugin_permission_model.json` y binding al `PluginRegistry` para bloquear permisos desconocidos o deny/critical en manifests. No se habilita ejecución de plugins, dynamic import, subprocess, red, filesystem write, pip install, marketplace ni remote execution.

Resultado POST-H-019-C: `implemented-initial`. Se agrega `PluginStaticValidator`, `PluginExposureReporter`, schema `PluginSandboxDesignReport` y `plugin dry-run --all --dry-run --write-report` para simular instalación metadata-only y producir exposure report. No se habilita ejecución de plugins, carga dinámica, subprocess, red, APIs externas, filesystem write, pip install, marketplace ni remote execution.

Resultado POST-H-019-D: `implemented-initial`. Se agrega `PluginSandboxQualityGate` y subgate `plugin-sandbox-design` a perfiles hardening/industrial para validar registry, permission model, exposure report y señal `plugin-ecosystem` sin cargar código de plugins ni ejecutar acciones externas.

Siguiente micro-sprint: `POST-H-019-E — Runbook, ADR trigger y cierre`.


## 1. Objetivo

Diseñar la arquitectura, contratos, threat model y validadores necesarios para un futuro ecosistema de plugins de DevPilot, manteniendo explícitamente bloqueada cualquier ejecución arbitraria de código.

El resultado de este hito debe ser un **diseño verificable y validadores de manifiestos**, no un motor de ejecución de plugins. La meta es reducir el riesgo de que `plugins/` o `.devpilot/plugins/` se interpreten como una capacidad ejecutable cuando todavía son metadata-only.

## 2. Contexto y justificación

El diagnóstico post-H identificó plugin registry como una capacidad `implemented-initial`/metadata-only y plugin execution como riesgo alto/crítico si se habilita sin sandbox. La arquitectura objetivo pospone plugins ejecutables hasta contar con diseño de aislamiento, permisos, firma, validación, policy binding, evals y test contracts.

Actualmente existen bases en:

```text
src/devpilot_core/plugins/
.devpilot/plugins/
docs/schemas/plugin_manifest.schema.json
src/devpilot_core/policy/
src/devpilot_core/approval/
src/devpilot_core/identity/
evals/fixtures/plugin_ecosystem_eval_cases.json
```

Este hito debe consolidar esas bases en un diseño formal, con validadores que impidan ejecutar código arbitrario y con gates que bloqueen cualquier evolución insegura.

## 3. Alcance

Incluye:

```text
- Threat model de plugins.
- Plugin sandbox design document.
- Plugin permission model.
- Manifest v2 o extensión de manifest actual.
- Plugin capability classification.
- Static validation de manifests.
- Dry-run de instalación simulada sin ejecutar código.
- Reporte de exposición de plugins.
- Quality gate que bloquee plugin execution.
- Runbook de operación metadata-only.
```

No incluye:

```text
- Ejecución de plugins.
- Carga dinámica de módulos externos.
- importlib de plugin code.
- subprocess para plugins.
- pip install de plugins.
- Marketplace de plugins.
- Firma remota.
- Descarga desde internet.
- Permitir arbitrary code execution.
- Remote execution.
```

## 4. Fuentes de entrada obligatorias

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/03_security/post_h_security_risk_register.md
docs/02_architecture/post_h_current_architecture_map.md
docs/05_operations/runbook.md
src/devpilot_core/plugins/
.devpilot/plugins/plugin_registry.json
docs/schemas/plugin_manifest.schema.json
src/devpilot_core/policy/
src/devpilot_core/approval/
src/devpilot_core/identity/
evals/fixtures/plugin_ecosystem_eval_cases.json
.devpilot/testing/test_contract_registry.json
```

## 5. Entregables

```text
docs/03_security/plugin_sandbox_threat_model.md
docs/02_architecture/plugin_sandbox_design.md
docs/05_operations/plugin_metadata_runbook.md
docs/schemas/plugin_permission_model.schema.json
docs/schemas/plugin_sandbox_design_report.schema.json
.devpilot/plugins/plugin_permission_model.json
src/devpilot_core/plugins/permission_model.py
src/devpilot_core/plugins/static_validator.py
src/devpilot_core/plugins/exposure_report.py
tests/test_post_h_019_plugin_permission_model.py
tests/test_post_h_019_plugin_static_validator.py
tests/test_post_h_019_plugin_execution_blocked.py
tests/test_post_h_019_plugin_quality_gate.py
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/plugins/registry.py
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

### 6.1 Plugin permission model

```json
{
  "schema_version": "1.0",
  "default_effect": "deny",
  "plugin_execution_allowed": false,
  "dynamic_import_allowed": false,
  "subprocess_allowed": false,
  "network_allowed": false,
  "filesystem_write_allowed": false,
  "permissions": [
    {
      "permission_id": "plugin.metadata.read",
      "description": "Read plugin manifest metadata only.",
      "effect": "allow",
      "risk_level": "low",
      "requires_approval": false
    },
    {
      "permission_id": "plugin.code.execute",
      "description": "Execute plugin-provided code.",
      "effect": "deny",
      "risk_level": "critical",
      "requires_approval": true,
      "blocked_until": "future-adr"
    }
  ]
}
```

### 6.2 Plugin exposure report

```json
{
  "schema_version": "1.0",
  "plugins_total": 3,
  "metadata_only_total": 3,
  "execution_allowed_total": 0,
  "critical_permissions_total": 0,
  "blocked_permissions_total": 1,
  "network_allowed": false,
  "dynamic_import_allowed": false,
  "subprocess_allowed": false,
  "blocking_findings_total": 0
}
```

## 7. Principios de diseño

```text
1. Metadata-only until proven safe.
2. No dynamic import of plugin code.
3. No subprocess for plugins.
4. No plugin marketplace.
5. No network for plugin discovery.
6. No filesystem writes by plugins.
7. Manifest validation is not execution permission.
8. Any future plugin execution requires new ADR, sandbox, tests, RBAC, approvals and rollback.
9. Plugin reports must separate declared, validated, install-simulated and executable states.
10. The safe default is deny.
```

## 8. Micro-sprints propuestos

### POST-H-019-A — Threat model y sandbox design

Objetivo: documentar amenazas, límites y arquitectura objetivo del futuro sandbox de plugins sin implementar ejecución.

Tareas:

```text
1. Crear docs/03_security/plugin_sandbox_threat_model.md.
2. Crear docs/02_architecture/plugin_sandbox_design.md.
3. Identificar amenazas: arbitrary code execution, dependency confusion, secret exfiltration, path traversal, persistence, network abuse.
4. Definir boundary: metadata-only, validator-only, no execution.
5. Definir future ADR requirements para cualquier ejecución.
6. Validar frontmatter de documentos.
```

Criterios PASS:

```text
PASS si threat model cubre al menos 10 amenazas.
PASS si el diseño declara plugin_execution_allowed=false.
PASS si se documentan no-go gates.
PASS si los documentos tienen frontmatter aprobado o revisable según convención.
```

Criterios BLOCK:

```text
BLOCK si el diseño habilita ejecución.
BLOCK si se propone import dinámico de plugins.
BLOCK si se omiten amenazas de secretos/red/filesystem.
```

### POST-H-019-B — Permission model y manifest hardening

Objetivo: formalizar permisos de plugins y endurecer manifest validation.

Tareas:

```text
1. Crear plugin_permission_model.schema.json.
2. Crear .devpilot/plugins/plugin_permission_model.json.
3. Implementar permission_model.py.
4. Ampliar static validation de manifest.
5. Validar permisos declarados contra allowlist/denylist.
6. Crear tests de permisos bloqueados.
```

Criterios PASS:

```text
PASS si plugin.code.execute está deny.
PASS si dynamic_import_allowed=false.
PASS si subprocess_allowed=false.
PASS si network_allowed=false.
PASS si manifests con permisos no reconocidos fallan.
```

Criterios BLOCK:

```text
BLOCK si un manifest puede declarar ejecución permitida.
BLOCK si permisos desconocidos son tolerados.
BLOCK si permisos críticos no exigen future ADR.
```

### POST-H-019-C — Install dry-run y exposure report

Objetivo: simular instalación metadata-only de plugins y producir reportes de exposición.

Tareas:

```text
1. Implementar static_validator.py.
2. Implementar exposure_report.py.
3. Agregar CLI plugin dry-run --plugin-id/--all --json si no existe o extenderlo.
4. Garantizar que dry-run no importe código ni lea archivos arbitrarios.
5. Generar plugin exposure report.
6. Agregar tests de no ejecución.
```

Criterios PASS:

```text
PASS si dry-run valida solo metadata.
PASS si no usa importlib para código externo.
PASS si exposure report muestra execution_allowed_total=0.
PASS si no hay network/external_api/mutations.
```

Criterios BLOCK:

```text
BLOCK si dry-run ejecuta código de plugin.
BLOCK si se permite instalar dependencias.
BLOCK si se escribe fuera de outputs/.devpilot permitidos.
```

### POST-H-019-D — Quality gate plugin safety

Objetivo: integrar seguridad de plugins a quality gate.

Tareas:

```text
1. Agregar subgate plugin-sandbox-design.
2. Validar plugin registry, permission model y exposure report.
3. Validar que plugin execution está bloqueado.
4. Integrar evals plugin-ecosystem existentes como señal preliminar.
5. Agregar test contract post-h-019-plugin-sandbox-design.
```

Criterios PASS:

```text
PASS si el subgate pasa con plugin_execution_allowed=false.
PASS si todos los plugin manifests son metadata-only.
PASS si test-contracts validate reconoce el contrato.
PASS si quality gate no usa red ni mutaciones.
```

Criterios BLOCK:

```text
BLOCK si plugin execution queda habilitado.
BLOCK si un plugin puede declarar permisos críticos sin bloqueo.
BLOCK si el quality gate no evalúa plugin registry.
```

### POST-H-019-E — Runbook, ADR trigger y cierre

Objetivo: documentar operación segura y criterios para una futura ADR de ejecución.

Tareas:

```text
1. Crear docs/05_operations/plugin_metadata_runbook.md.
2. Documentar comandos de validación/dry-run.
3. Definir condiciones para futura ADR de plugin execution.
4. Actualizar roadmap notes si aplica, sin adelantar ejecución.
5. Ejecutar pruebas focales y gate.
```

Criterios PASS:

```text
PASS si el runbook explica metadata-only.
PASS si el ADR trigger exige sandbox, RBAC, approvals, tests y rollback.
PASS si no se declara plugin execution disponible.
```

Criterios BLOCK:

```text
BLOCK si el runbook incluye pasos para ejecutar plugins.
BLOCK si se sugiere pip install automático.
BLOCK si se omite la necesidad de ADR futura.
```

## 9. Comandos esperados de validación

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_post_h_019_plugin_permission_model.py -q
python -m pytest tests/test_post_h_019_plugin_static_validator.py -q
python -m pytest tests/test_post_h_019_plugin_execution_blocked.py -q
python -m pytest tests/test_post_h_019_plugin_quality_gate.py -q
python -m devpilot_core plugin validate --json
python -m devpilot_core plugin dry-run --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Arbitrary code execution | Crítica | No execution + tests de bloqueo. |
| Dependency confusion | Alta | No pip install / no marketplace. |
| Secret exfiltration | Alta | No network + SecretGuard. |
| Path traversal | Alta | PathGuard + metadata-only. |
| Sobreclaim de plugin support | Media-alta | Reportes separan metadata vs execution. |

## 11. No-go gates

```text
NO-GO si se habilita plugin execution.
NO-GO si se usa importlib para cargar código externo.
NO-GO si se permite subprocess.
NO-GO si se permite network.
NO-GO si se instala dependencia externa.
NO-GO si se omite threat model.
```

## 12. Definition of Done

```text
- Threat model creado.
- Sandbox design document creado.
- Permission model validable.
- Manifest/static validation endurecida.
- Dry-run metadata-only probado.
- Exposure report generado.
- Quality gate actualizado.
- Runbook creado.
- Test contract agregado.
- Plugin execution sigue bloqueado.
```
