---
doc_id: "POST-H-010-OBSERVABILITY-RETENTION-RUNBOOK"
title: "POST-H-010 — Observability retention local runbook"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
phase: "POST-FASE-H"
source_of_truth: true
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
---

# POST-H-010 — Observability retention local runbook

## Propósito

Este runbook operacionaliza la línea `POST-H-010 — Observability retention local`. Su objetivo es que un operador pueda verificar, inventariar, planear limpieza, exportar evidencia redactada y validar el gate de higiene de observabilidad sin depender de red, APIs externas, backends remotos de observabilidad ni acciones destructivas.

Esta versión es `implemented-initial`: cubre política local, inventario read-only, cleanup plan dry-run, export local redactado y subgate de quality-gate. No declara production-ready completo; firma/cifrado de export, DLP industrial profundo y ejecución real de cleanup quedan para hardening posterior.

## Principios operativos

```text
- Local-first por defecto.
- Dry-run/read-only para inventario y gate.
- Cleanup real deshabilitado.
- Export remoto deshabilitado.
- Redacción obligatoria para export.
- No incluir outputs/, .devpilot/devpilot.db ni .devpilot/agent_sessions/ en ZIPs limpios.
- No versionar artefactos runtime de observabilidad.
```

## Artefactos principales

```text
.devpilot/observability/retention_policy.json
src/devpilot_core/observability/retention.py
src/devpilot_core/observability/inventory.py
src/devpilot_core/observability/cleanup.py
src/devpilot_core/observability/export.py
src/devpilot_core/observability/hygiene.py
docs/schemas/observability_retention_policy.schema.json
docs/schemas/observability_inventory.schema.json
docs/schemas/observability_cleanup_plan.schema.json
docs/schemas/observability_redacted_export.schema.json
docs/schemas/observability_retention_hygiene.schema.json
```

## Comandos de mantenimiento local

### 1. Validar la política de retención

```powershell
python -m devpilot_core schema validate --schema-id ObservabilityRetentionPolicy --instance .devpilot/observability/retention_policy.json --json
```

PASS esperado:

```text
ok=true
errors_total=0
network_used=false
external_api_used=false
```

### 2. Generar inventario read-only

```powershell
python -m devpilot_core observability inventory --json --write-report
```

Produce, solo cuando se usa `--write-report`:

```text
outputs/reports/observability_inventory.json
outputs/reports/observability_inventory.md
```

Los targets ausentes en un ZIP limpio de fuente son warnings operacionales, no bloqueo. El inventario no lee payloads crudos.

### 3. Generar cleanup plan dry-run

```powershell
python -m devpilot_core observability cleanup-plan --json --write-report
```

El comando calcula acciones `would_rotate`, `would_delete`, `would_archive`, `would_redact` y `would_export`, pero no ejecuta ninguna mutación. El uso de `--execute` en este comando debe bloquear.

Safety probe:

```powershell
python -m devpilot_core observability cleanup-plan --json --execute
```

Resultado esperado:

```text
ok=false
exit_code=2
mutations_performed=false
destructive_cleanup_performed=false
```

### 4. Exportar evidencia local redactada

```powershell
python -m devpilot_core observability export --redacted --json --write-report
```

Produce evidencia local bajo:

```text
outputs/reports/observability_redacted_export.json
outputs/reports/observability_redacted_export.md
outputs/audit_exports/observability_redacted_export/
```

El export debe mantener:

```text
raw_prompts_exported=false
raw_outputs_exported=false
secrets_exported=false
env_files_exported=false
sqlite_raw_exported=false
remote_export_enabled=false
```

### 5. Ejecutar gate de retención e higiene

```powershell
python -m devpilot_core quality-gate run --profile hardening --json
```

El perfil hardening debe incluir el subgate:

```text
observability-retention
```

PASS esperado:

```text
observability_retention_hygiene_passed=true
policy_validation_passed=true
inventory_validation_passed=true
clean_zip_hygiene_passed=true
network_used=false
external_api_used=false
mutations_performed=false
```

## Criterios PASS/BLOCK

PASS:

```text
- Política local válida.
- Inventario metadata-only sin findings bloqueantes.
- ZIP hygiene excluye outputs/, .devpilot/devpilot.db y .devpilot/agent_sessions/.
- Export local requiere redacción.
- Quality-gate hardening contiene observability-retention.
```

BLOCK:

```text
- remote_export_enabled=true.
- raw prompts/outputs permitidos o exportados.
- Secrets, .env o SQLite crudo incluidos en export.
- Runtime observability targets marcados como versionable/source_of_truth.
- outputs/, .devpilot/devpilot.db o .devpilot/agent_sessions/ entran a un ZIP limpio de fuente.
- El gate requiere red/API externa o depende de outputs efímeros para pasar.
```

## Comandos de validación focal

```powershell
python -m pytest -p no:ddtrace tests/test_observability_hygiene_gate.py tests/test_post_h_010_observability_retention.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core docs-governance validate --json
```

## Limitaciones y evolución pendiente

```text
- No hay cleanup real; solo planificación dry-run.
- No hay export remoto.
- No hay firma/cifrado del audit export.
- No hay DLP industrial completo; la redacción actual es determinística y conservadora.
- POST-H-010 cierra como implemented-initial; producción estricta requiere POST-H-013/POST-H-025 y hardening adicional.
```
