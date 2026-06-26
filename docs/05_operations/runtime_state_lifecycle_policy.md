---
doc_id: "DEVPL-RUNTIME-STATE-LIFECYCLE-POLICY"
id: "POST-H-008-A"
title: "Runtime state lifecycle policy"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-25"
phase: "POST-FASE-H"
local_first: true
dry_run: true
no_remote_execution_enabled: true
implementation_status: "implemented-initial"
---

# Runtime state lifecycle policy

## 1. Propósito

Este documento operacionaliza `POST-H-008-A — Taxonomía y policy schema` y define la taxonomía inicial de **runtime state** para DevPilot Local.

La versión actual es `implemented-initial`: declara política, schemas y criterios de higiene, pero todavía no implementa comandos de inventario, limpieza o exportación. Esos comportamientos corresponden a los micro-sprints `POST-H-008-B`, `POST-H-008-C` y `POST-H-008-D`.

## 2. Fuente de verdad

| Artefacto | Rol | Versionable |
|---|---|---:|
| `.devpilot/runtime_state_policy.json` | Política declarativa local | Sí |
| `docs/schemas/runtime_state_policy.schema.json` | Contrato estructural de policy | Sí |
| `docs/schemas/runtime_state_inventory.schema.json` | Contrato futuro de inventory read-only | Sí |
| `docs/POST-H-008_runtime_state_lifecycle.md` | Backlog aprobado | Sí |

## 3. Taxonomía inicial

| Clase | Ejemplos | Source of truth | Versionable | Cleanup |
|---|---|---:|---:|---:|
| `source-code` | `src/**/*.py`, `tests/**/*.py` | Sí | Sí | No |
| `engineering-docs` | `docs/**/*.md`, `README.md` | Sí | Sí | No |
| `runtime-policy` | `.devpilot/runtime_state_policy.json`, `.devpilot/project_state.json` | Sí | Sí | No |
| `generated-reports` | `outputs/reports/**/*` | No | No | Sí, con política |
| `trace-events` | `outputs/traces/**/*` | No | No | Sí, con redacción |
| `eval-outputs` | `outputs/evals/**/*` | No | No | Sí, con redacción |
| `draft-outputs` | `outputs/drafts/**/*` | No | No | Sí, con redacción |
| `local-db` | `.devpilot/devpilot.db` | No | No | No automático |
| `agent-sessions` | `.devpilot/agent_sessions/**/*` | No | No | Sí, con redacción |
| `rag-index` | `.devpilot/rag/docs_index.json` | Condicional | Sí | No automático |
| `python-caches` | `.pytest_cache`, `__pycache__`, `*.pyc` | No | No | Sí |
| `node-artifacts` | `node_modules`, `ui/web/dist` | No | No | Sí |
| `release-evidence` | manifests, changelog, audit reports | Sí | Sí | No |

## 4. Reglas de ZIP limpio

Los ZIPs entregables generados desde DevPilot deben excluir como mínimo:

```text
outputs/
.devpilot/devpilot.db
.devpilot/agent_sessions/
.pytest_cache/
__pycache__/
node_modules/
ui/web/dist/
*.pyc
*.pyo
```

La forma preferida para empaquetar fuente limpia sigue siendo `git archive` o un empaquetador equivalente que excluya runtime state. La excepción explícita son los ZIPs que el owner sube como evidencia de ejecución: esos sí pueden contener `outputs/` o `.devpilot/devpilot.db` para auditoría local.

## 5. Reglas de seguridad

```text
destructive_cleanup_default = false
requires_execute_flag = true
source_of_truth_never_delete = true
network_required = false
external_api_required = false
remote_backup_enabled = false
```

Cualquier futura limpieza destructiva debe permanecer en dry-run por defecto, separar `safe-cleanup`, `requires-approval` y `never-delete`, y no debe borrar `src/`, `tests/`, `docs/`, project state ni contratos.

## 6. Validación local

```powershell
$env:PYTHONPATH="src"
$env:DD_TRACE_ENABLED="false"

python -m pytest tests/test_runtime_state_policy_schema.py -q
python -m pytest tests/test_post_h_008_runtime_state_lifecycle.py tests/test_schema_registry.py -q
python -m devpilot_core schema validate --schema-id RuntimeStatePolicy --instance .devpilot/runtime_state_policy.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

## 7. Estado y evolución

`POST-H-008-A` no añade comandos runtime ni modifica archivos generados. La evolución prevista es:

```text
POST-H-008-B — Runtime state inventory read-only
POST-H-008-C — Cleanup plan dry-run
POST-H-008-D — Export y redacción de evidencia runtime
POST-H-008-E — Gate de higiene runtime y release archive
```
