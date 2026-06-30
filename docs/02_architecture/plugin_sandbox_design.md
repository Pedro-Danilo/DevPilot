---
doc_id: "POST-H-019-PLUGIN-SANDBOX-DESIGN"
title: "POST-H-019 — Plugin sandbox design"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
source_of_truth: true
preliminary: true
---

# POST-H-019 — Plugin sandbox design

## Decisión de diseño vigente

DevPilot tratará los plugins como **metadata gobernada** hasta que una ADR futura autorice otro estado. POST-H-019-A no implementa motor de ejecución: solo define arquitectura, límites y requisitos de evolución.

```text
plugin_execution_allowed=false
dynamic_import_allowed=false
subprocess_allowed=false
network_allowed=false
external_api_allowed=false
filesystem_write_allowed=false
remote_execution_allowed=false
marketplace_enabled=false
pip_install_allowed=false
metadata_only=true
validator_only=true
```

## Modelo conceptual

```text
.devpilot/plugins/plugin_registry.json
        │
        ▼
Plugin Manifest / Registry metadata
        │  no importlib, no subprocess, no pip install
        ▼
Static validation / permission model / exposure report
        │
        ▼
PolicyEngine + Approval + RBAC + MIASI binding
        │
        ▼
Quality gate plugin-sandbox-design
        │
        ▼
Estado permitido en POST-H-019: validated metadata only
```

La frontera central es: `registered != installable != executable`. Un plugin puede estar declarado y validado sin ser instalable ni ejecutable.

## Componentes objetivo por micro-sprint

| Componente | POST-H-019-A | Evolución prevista |
|---|---|---|
| Threat model | Creado y aprobado | Se ampliará con pruebas adversariales. |
| Sandbox design | Creado y aprobado | Se conectará a permission model y quality gate. |
| Permission model | Diseñado conceptualmente | POST-H-019-B lo formaliza como JSON/schema. |
| Static validator | Definido como boundary | POST-H-019-B/C lo implementan/endurecen. |
| Dry-run metadata-only | Ya existe base histórica; no se amplía en A | POST-H-019-C lo consolida. |
| Exposure report | Diseñado conceptualmente | POST-H-019-C lo implementa. |
| Quality gate | Diseñado conceptualmente | POST-H-019-D lo integra. |
| Runbook | Requisito definido | POST-H-019-E lo crea/cierra. |

## Policy boundary

El diseño exige defaults seguros:

```text
default_effect=deny
plugin_execution_allowed=false
dynamic_import_allowed=false
subprocess_allowed=false
network_allowed=false
filesystem_write_allowed=false
unknown_permissions=block
critical_permissions=require_future_adr
manifest_validation_is_not_execution_permission=true
```

## Estados permitidos

```text
registered: metadata existe en registry local.
validated: metadata pasa schema/static checks.
dry_run_simulated: operación metadata-only reportada sin ejecutar código.
executable: no disponible en POST-H-019.
```

Los reportes deben declarar explícitamente `execution_allowed_total=0` mientras no exista ADR futura.

## Estados bloqueados

```text
importable_entrypoint
python_module_loading
subprocess_spawn
shell_command
network_discovery
external_api_call
pip_install
marketplace_download
filesystem_write_by_plugin
remote_execution
```

## Requisitos para ADR futura de ejecución

Una ADR futura debe responder y probar, como mínimo:

```text
1. Aislamiento técnico: proceso, contenedor, WASM u otro mecanismo verificable.
2. Modelo de permisos granular y deny-by-default.
3. Firma/verificación local o equivalente supply-chain.
4. PolicyEngine/Approval/RBAC obligatorio para permisos críticos.
5. SecretGuard/PathGuard/ToolInjectionGuard aplicados antes de ejecución.
6. Red, filesystem write y subprocess deshabilitados por defecto.
7. Observabilidad, audit trail, rollback y kill switch.
8. Evals adversariales y tests de no-regresión.
9. Runbook operativo y procedimiento de revocación.
10. Quality gate que bloquee cualquier permiso crítico no aprobado.
```

## No-go gates de diseño

```text
BLOCK si el diseño habilita ejecución.
BLOCK si se propone import dinámico de plugins.
BLOCK si se propone subprocess/shell para plugins.
BLOCK si se permite red o APIs externas por defecto.
BLOCK si se omite amenaza de secretos, filesystem o path traversal.
BLOCK si se confunde validación de manifest con autorización de ejecución.
```

## Integración con arquitectura actual

POST-H-019-A se apoya en los componentes existentes `src/devpilot_core/plugins/`, `.devpilot/plugins/plugin_registry.json`, `docs/schemas/plugin_manifest.schema.json`, PolicyEngine, Approval, RBAC, MIASI y Test Contract Registry. La integración sigue siendo local-first y dry-run; no agrega dependencias externas ni cambia el runtime de plugins.

## Estado

Este diseño es `implemented-initial` y preliminar. Sirve para bloquear ambigüedades y preparar POST-H-019-B/C/D/E. No declara disponibilidad productiva de plugins ejecutables.
